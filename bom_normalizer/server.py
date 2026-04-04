"""
FastAPI Server
HTTP API for BOM Normalizer Environment
"""

import os
import json
import pandas as pd
from contextlib import asynccontextmanager
from typing import Dict
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import OpenAI

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[SERVER] Loaded .env file")
except ImportError:
    print("[SERVER] python-dotenv not installed, using system environment variables")

from .env import BOMEnv
from .models import Action, Observation, StepResponse, BOMRow


# Environment store
env_store: Dict[str, BOMEnv] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    # Startup: Initialize environments
    for task in ('easy', 'medium', 'hard'):
        env_store[task] = BOMEnv(task_id=task, seed=42)
    
    yield
    
    # Shutdown: Cleanup
    env_store.clear()


# Create FastAPI app
app = FastAPI(
    title='BOM Normalizer Environment',
    description='OpenEnv agent training environment for BOM normalization',
    version='1.0.0',
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)


@app.get('/health')
async def health():
    """Health check endpoint"""
    return {'status': 'ok', 'version': '1.0.0'}


@app.get('/tasks')
async def get_tasks():
    """Get list of available tasks"""
    return {
        'tasks': ['easy', 'medium', 'hard'],
        'descriptions': {
            'easy': 'Normalize vendor names across 10 BOM rows',
            'medium': 'Normalize vendor, value, and package across 50 rows',
            'hard': 'Full normalization + deduplication across 100 rows including edge cases and duplicates'
        }
    }


@app.post('/reset')
async def reset(task_id: str = Query('easy', description='Task ID (easy/medium/hard)')):
    """
    Reset environment and start new episode
    
    Args:
        task_id: Task identifier
    
    Returns:
        Initial observation
    """
    if task_id not in env_store:
        raise HTTPException(status_code=400, detail=f'Unknown task_id: {task_id}')
    
    env = env_store[task_id]
    obs = env.reset()
    
    return obs


@app.post('/step')
async def step(
    action: Action,
    task_id: str = Query('easy', description='Task ID (easy/medium/hard)')
) -> StepResponse:
    """
    Execute one step in the environment
    
    Args:
        action: Action to execute
        task_id: Task identifier
    
    Returns:
        Step response with observation, reward, done, info
    """
    if task_id not in env_store:
        raise HTTPException(status_code=400, detail=f'Unknown task_id: {task_id}')
    
    env = env_store[task_id]
    
    try:
        obs, reward, done, info = env.step(action)
        
        return StepResponse(
            observation=obs,
            reward=reward,
            done=done,
            info=info
        )
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get('/state')
async def get_state(task_id: str = Query('easy', description='Task ID (easy/medium/hard)')):
    """
    Get current state without advancing episode
    
    Args:
        task_id: Task identifier
    
    Returns:
        Current observation
    """
    if task_id not in env_store:
        raise HTTPException(status_code=400, detail=f'Unknown task_id: {task_id}')
    
    env = env_store[task_id]
    obs = env.state()
    
    return obs


@app.post('/upload-bom')
async def upload_bom(
    file: UploadFile = File(...),
    task_id: str = Query('easy', description='Task ID')
):
    """
    Upload Excel/CSV file and load as BOM data
    
    Args:
        file: Excel or CSV file
        task_id: Task identifier
    
    Returns:
        Initial observation with uploaded data
    """
    if task_id not in env_store:
        raise HTTPException(status_code=400, detail=f'Unknown task_id: {task_id}')
    
    try:
        # Read file
        contents = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(pd.io.common.BytesIO(contents))
        else:
            df = pd.read_excel(pd.io.common.BytesIO(contents))
        
        # Validate columns
        required_cols = ['vendor_name', 'part_number', 'value', 'package', 'quantity']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            # Try common variations
            col_mapping = {
                'vendor': 'vendor_name',
                'vendor name': 'vendor_name',
                'part': 'part_number',
                'part number': 'part_number',
                'qty': 'quantity',
                'pkg': 'package'
            }
            
            df.columns = [col_mapping.get(col.lower(), col) for col in df.columns]
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                raise HTTPException(
                    status_code=400,
                    detail=f'Missing required columns: {missing_cols}'
                )
        
        # Load into environment
        env = env_store[task_id]
        env.reset()
        
        # Replace generated rows with uploaded data
        env.current_bom = []
        for idx, row in df.iterrows():
            bom_row = BOMRow(
                row_id=idx,
                vendor_name=str(row['vendor_name']),
                part_number=str(row['part_number']),
                value=str(row['value']),
                package=str(row['package']),
                quantity=int(row['quantity']),
                status='raw',
                merged_into=None
            )
            env.current_bom.append(bom_row)
        
        obs = env.state()
        return obs
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Failed to process file: {str(e)}')


@app.post('/auto-normalize')
async def auto_normalize(
    task_id: str = Query('easy', description='Task ID')
):
    """
    Auto-normalize BOM using AI/LLM (simplified version)
    
    Args:
        task_id: Task identifier
    
    Returns:
        Final observation after normalization
    """
    if task_id not in env_store:
        raise HTTPException(status_code=400, detail=f'Unknown task_id: {task_id}')
    
    env = env_store[task_id]
    
    # Get API configuration from environment
    api_key = os.getenv('OPENAI_API_KEY', 'dummy')
    api_base_url = os.getenv('API_BASE_URL', 'http://localhost:11434/v1')
    model_name = os.getenv('MODEL_NAME', 'llama3.2')
    
    print(f"[AUTO-NORMALIZE] Configuration:")
    print(f"  API Base URL: {api_base_url}")
    print(f"  Model Name: {model_name}")
    print(f"  API Key: {'*' * len(api_key) if api_key else 'None'}")
    
    # Initialize OpenAI client
    if 'openai.com' in api_base_url:
        client = OpenAI(api_key=api_key)
    else:
        client = OpenAI(base_url=api_base_url, api_key=api_key)
    
    system_prompt = """You are a BOM normalization AI agent.
Your job is to normalize vendor names, values, and packages to their CANONICAL forms.

CRITICAL RULES:
1. NEVER submit until fields_remaining = 0
2. Normalize ALL variations of a vendor to the SAME canonical name
3. Process rows one at a time with specific actions
4. RESPOND WITH ONLY JSON - NO explanatory text, NO markdown, JUST the JSON object

Vendor normalizations (MUST use these exact canonical names):
- "TI", "T.I.", "Texas Inst.", "Texas Instruments Inc" → "Texas Instruments"
- "Murata", "Murata Mfg", "MURATA" → "Murata Manufacturing"  
- "ST", "STMicro", "ST Micro" → "STMicroelectronics"
- "Vishay" → "Vishay Intertechnology"

Value normalizations:
- "10K", "10k", "10 kohm" → "10000"
- "100nF", "100 nanofarad" → "100e-9"
- "10uF", "10 microfarad" → "10e-6"

Package normalizations:
- "SOT23", "SOT23-3", "SOT-23-3" → "SOT-23"
- "0402M", "0402 SMD" → "0402"

RESPONSE FORMAT (JSON ONLY - no other text):
{"action_type": "normalize_vendor", "row_id": 1, "new_value": "Texas Instruments"}
{"action_type": "normalize_value", "row_id": 1, "new_value": "10000"}
{"action_type": "normalize_package", "row_id": 1, "new_value": "SOT-23"}
{"action_type": "submit"} - ONLY when fields_remaining = 0"""
    
    max_steps = 100  # Increased to ensure completion
    steps_taken = 0
    errors = []
    
    for step in range(max_steps):
        obs = env.state()
        
        # Check if done
        if obs.done:
            break
        
        # Check if all fields normalized
        if obs.fields_remaining == 0:
            # Submit
            env.step(Action(action_type='submit'))
            break
        
        # Get ALL rows to show complete picture
        rows_str = json.dumps([{
            'row_id': r.row_id,
            'vendor_name': r.vendor_name,
            'value': r.value,
            'package': r.package,
            'status': r.status
        } for r in obs.rows], indent=2)
        
        user_prompt = f"""Step {step + 1}/{max_steps}
Fields remaining: {obs.fields_remaining}
Total rows: {len(obs.rows)}

ALL ROWS:
{rows_str}

IMPORTANT: You must normalize ALL fields in ALL rows before submitting. Fields remaining = {obs.fields_remaining}
Choose ONE action to normalize a field in one row."""
        
        try:
            # Call LLM
            log_file = open("auto_normalize_debug.log", "a")
            log_file.write(f"\n[AUTO-NORMALIZE] Step {step + 1}: Calling LLM...\n")
            log_file.write(f"[AUTO-NORMALIZE] User prompt preview: {user_prompt[:200]}...\n")
            log_file.flush()
            
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                temperature=0.0,
                max_tokens=100
            )
            
            log_file.write(f"[AUTO-NORMALIZE] Step {step + 1}: LLM call completed\n")
            log_file.flush()
            
            if not response or not response.choices or len(response.choices) == 0:
                log_file.write(f"[AUTO-NORMALIZE] ERROR: LLM returned no choices\n")
                log_file.close()
                raise ValueError("LLM returned no choices")
            
            response_text = response.choices[0].message.content
            
            if response_text is None:
                log_file.write(f"[AUTO-NORMALIZE] ERROR: LLM returned None content\n")
                log_file.close()
                raise ValueError("LLM returned None content")
            
            response_text = response_text.strip()
            log_file.write(f"[AUTO-NORMALIZE] Step {step + 1}: Response text: '{response_text}'\n")
            log_file.write(f"[AUTO-NORMALIZE] Step {step + 1}: Response length: {len(response_text)}\n")
            log_file.flush()
            
            if not response_text:
                log_file.close()
                raise ValueError("LLM returned empty response")
            
            # Parse action - extract JSON from response
            log_file.write(f"[AUTO-NORMALIZE] Step {step + 1}: Parsing JSON...\n")
            
            # Remove markdown code blocks if present
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            # Extract JSON object from text (handle explanatory text before/after JSON)
            import re
            json_match = re.search(r'\{[^}]+\}', response_text)
            if json_match:
                response_text = json_match.group(0)
            
            log_file.write(f"[AUTO-NORMALIZE] Step {step + 1}: Cleaned response: '{response_text}'\n")
            log_file.flush()
            action_dict = json.loads(response_text)
            log_file.close()
            action = Action(**action_dict)
            
            # Execute action
            print(f"[AUTO-NORMALIZE] Step {step + 1}: Executing action: {action.action_type}")
            env.step(action)
            steps_taken += 1
            print(f"[AUTO-NORMALIZE] Step {step + 1}: Complete. Fields remaining: {env.state().fields_remaining}")
            
        except Exception as e:
            error_msg = f"AI error at step {step}: {e}"
            print(f"[AUTO-NORMALIZE] {error_msg}")
            import traceback
            traceback.print_exc()
            errors.append(error_msg)
            break
    
    final_obs = env.state()
    return {
        'success': True,
        'steps': steps_taken,
        'final_observation': final_obs,
        'errors': errors
    }


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=7860)
