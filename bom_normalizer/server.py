"""
FastAPI Server
HTTP API for BOM Normalizer Environment
"""

import logging
import os
import re
import json
import pandas as pd
from contextlib import asynccontextmanager
from typing import Dict
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import OpenAI

logger = logging.getLogger(__name__)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Loaded .env file")
except ImportError:
    logger.info("python-dotenv not installed, using system environment variables")

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


@app.get('/')
async def root():
    """Root endpoint - API information"""
    return {
        'name': 'BOM Normalizer Environment',
        'version': '1.0.0',
        'description': 'OpenEnv agent training environment for BOM normalization',
        'endpoints': {
            'health': '/health',
            'tasks': '/tasks',
            'reset': '/reset',
            'step': '/step',
            'state': '/state',
            'docs': '/docs'
        },
        'status': 'running'
    }


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
        contents = await file.read()
        import io

        fname = (file.filename or '').lower()
        if fname.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))

        # ── Normalise column names: lowercase + strip whitespace/underscores ──
        # Build a flexible alias table so virtually any common header works.
        alias_map: dict[str, str] = {
            # vendor_name
            'vendor_name': 'vendor_name', 'vendor name': 'vendor_name',
            'vendor': 'vendor_name', 'manufacturer': 'vendor_name',
            'mfr': 'vendor_name', 'mfg': 'vendor_name', 'supplier': 'vendor_name',
            'brand': 'vendor_name', 'company': 'vendor_name',
            # part_number
            'part_number': 'part_number', 'part number': 'part_number',
            'part': 'part_number', 'part no': 'part_number',
            'part no.': 'part_number', 'part#': 'part_number',
            'mpn': 'part_number', 'mfr part number': 'part_number',
            'mfr part no': 'part_number', 'item': 'part_number',
            'sku': 'part_number', 'component': 'part_number',
            # value
            'value': 'value', 'val': 'value', 'component value': 'value',
            'rating': 'value', 'spec': 'value',
            # package
            'package': 'package', 'pkg': 'package', 'footprint': 'package',
            'case': 'package', 'size': 'package', 'form factor': 'package',
            # quantity
            'quantity': 'quantity', 'qty': 'quantity', 'count': 'quantity',
            'amount': 'quantity', 'num': 'quantity', 'number': 'quantity',
            'units': 'quantity',
        }

        def normalise_col(col: str) -> str:
            key = col.strip().lower().replace('_', ' ')
            return alias_map.get(key, col.strip().lower().replace(' ', '_'))

        df.columns = [normalise_col(c) for c in df.columns]

        required_cols = ['vendor_name', 'part_number', 'value', 'package', 'quantity']
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            found = list(df.columns)
            raise HTTPException(
                status_code=400,
                detail=(
                    f'Missing required columns: {missing_cols}. '
                    f'Your file has: {found}. '
                    f'Please use the Template button to download a correctly-formatted file.'
                )
            )

        # Drop completely empty rows
        df = df.dropna(subset=['vendor_name', 'part_number'], how='all')
        df = df.reset_index(drop=True)

        if len(df) == 0:
            raise HTTPException(status_code=400, detail='The uploaded file has no data rows.')

        # Load into environment
        env = env_store[task_id]
        env.reset()
        env.current_bom = []
        for idx, row in df.iterrows():
            try:
                qty = int(float(str(row['quantity']).replace(',', '')))
            except (ValueError, TypeError):
                qty = 1
            bom_row = BOMRow(
                row_id=int(idx) + 1,
                vendor_name=str(row['vendor_name']).strip(),
                part_number=str(row['part_number']).strip(),
                value=str(row.get('value', '')).strip(),
                package=str(row.get('package', '')).strip(),
                quantity=qty,
                status='raw',
                merged_into=None
            )
            env.current_bom.append(bom_row)

        obs = env.state()
        return obs

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Failed to process file: {str(e)}')


@app.get('/download-template')
async def download_template():
    """Return a sample Excel BOM template the user can fill in."""
    import io
    from fastapi.responses import StreamingResponse
    sample_data = {
        'vendor_name':  ['Texas Instruments', 'Murata Manufacturing', 'Vishay Dale', 'Samsung Electro-Mechanics', 'Yageo'],
        'part_number':  ['SN74HC00N',          'GRM188R71H104KA93D',  'CRCW040210K0FKED', 'CL10A106KP8NNNC', 'RC0402FR-0710KL'],
        'value':        ['5V',                  '100nF',               '10K',              '10uF',             '10K'],
        'package':      ['DIP14',               '0402',                '0402',             '0603',             '0402'],
        'quantity':     [10,                    100,                   50,                 60,                  80],
    }
    df = pd.DataFrame(sample_data)
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    headers = {'Content-Disposition': 'attachment; filename="bom_template.xlsx"'}
    return StreamingResponse(
        buf,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers=headers
    )


@app.post('/auto-normalize')
async def auto_normalize(
    task_id: str = Query('easy', description='Task ID')
):
    """
    Auto-normalize BOM using AI/LLM
    
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
    
    # Initialize OpenAI client
    if 'openai.com' in api_base_url:
        client = OpenAI(api_key=api_key)
    else:
        client = OpenAI(base_url=api_base_url, api_key=api_key)
    
    system_prompt = """You are a BOM (Bill of Materials) normalization AI agent for electronics manufacturing.
Normalize vendor names, values, packages, and part numbers to their CANONICAL forms.

CRITICAL RULES:
1. RESPOND WITH ONLY A SINGLE JSON OBJECT — no text, no markdown, no explanation
2. Never submit until fields_remaining = 0
3. Prefer batch_normalize to fix many rows at once (very efficient)

VENDOR CANONICAL NAMES (use EXACTLY these):
- "TI", "T.I.", "Texas Inst.", "Texas Instruments Inc" → "Texas Instruments"
- "Murata", "Murata Mfg", "Murata Mfg Co", "MURATA" → "Murata Manufacturing"
- "ST", "STMicro", "ST Micro", "STMicroelectronics NV" → "STMicroelectronics"
- "Vishay", "Vishay Dale" → "Vishay Intertechnology"
- "ON Semi", "ON Semi.", "OnSemi", "Fairchild" → "ON Semiconductor"
- "NXP", "NXP Semi", "Freescale" → "NXP Semiconductors"
- "Infineon", "Infineon Tech", "IFX", "Infinion" → "Infineon Technologies"
- "Renesas", "Renesas Elec" → "Renesas Electronics"
- "ADI", "Analog Dev", "Linear Technology" → "Analog Devices"
- "Microchip", "MCHP", "Atmel" → "Microchip Technology"
- "Maxim", "Maxim Int" → "Maxim Integrated"
- "Cypress", "Cypress Semi" → "Cypress Semiconductor"
- "Broadcom", "Avago" → "Broadcom"
- "ROHM", "Rohm" → "Rohm Semiconductor"
- "Pana", "Matsushita" → "Panasonic"
- "TDK", "TDK Corp" → "TDK Corporation"
- "Samsung", "SEC", "SAMSUNG", "Samsung Electro" → "Samsung Electro-Mechanics"

VALUE NORMALIZATIONS:
- "10K", "10k", "10kΩ", "10kohm" → "10000"
- "1K", "1k" → "1000"
- "100K" → "100000"
- "1M", "1MΩ" → "1000000"
- "100nF", "0.1uF" → "100e-9"
- "10uF", "10µF" → "10e-6"
- "1uF" → "1e-6"
- "22uF" → "22e-6"
- "1000pF" → "1e-9"
- "5V", "5.0V" → "5"
- "3.3V" → "3.3"

PACKAGE NORMALIZATIONS:
- "SOT23", "SOT23-3", "sot 23" → "SOT-23"
- "DIP14", "dip 14", "DIP 14" → "DIP-14"
- "DIP8", "dip 8", "DIP 8" → "DIP-8"
- "SOIC8", "SOIC 8" → "SOIC-8"
- "TO92", "TO 92" → "TO-92"
- "TO220", "TO 220" → "TO-220"
- "DO35", "DO 35" → "DO-35"
- "QFN56" → "QFN-56"
- "LQFP48" → "LQFP-48"
- "LQFP100" → "LQFP-100"

AVAILABLE ACTIONS (choose the most efficient):
{"action_type": "batch_normalize", "field": "vendor_name", "from_value": "TI", "new_value": "Texas Instruments"}
{"action_type": "normalize_vendor", "row_id": 1, "new_value": "Texas Instruments"}
{"action_type": "normalize_value", "row_id": 2, "new_value": "10000"}
{"action_type": "normalize_package", "row_id": 3, "new_value": "SOT-23"}
{"action_type": "normalize_part", "row_id": 4, "new_value": "SN74HC00N"}
{"action_type": "submit"}"""

    # FIX 1: Use the task's actual max_steps, not a hardcoded 100
    obs_init = env.state()
    max_steps = obs_init.max_steps
    steps_taken = 0
    errors = []
    consecutive_failures = 0

    for step in range(max_steps):
        obs = env.state()

        if obs.done:
            break

        if obs.fields_remaining == 0:
            env.step(Action(action_type='submit'))
            break

        # FIX 2: Only send RAW rows (not already normalized), limit to 20 at a time
        raw_rows = [r for r in obs.rows if r.status == 'raw']
        batch = raw_rows[:20]

        rows_str = json.dumps([{
            'row_id': r.row_id,
            'vendor_name': r.vendor_name,
            'part_number': r.part_number,
            'value': r.value,
            'package': r.package
        } for r in batch], indent=2)

        # Show unique raw vendor names to encourage batch_normalize
        unique_vendors = list({r.vendor_name for r in raw_rows})[:15]

        user_prompt = f"""Step {step + 1}/{max_steps} | Fields remaining: {obs.fields_remaining} | RAW rows left: {len(raw_rows)}

Unique raw vendor names: {unique_vendors}

Next 20 RAW rows to fix:
{rows_str}

Pick the MOST EFFICIENT action. Use batch_normalize when multiple rows share the same wrong value.
Respond with ONE JSON object only."""

        try:
            logger.debug("Step %d: Calling LLM, %d fields remaining", step + 1, obs.fields_remaining)

            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                temperature=0.0,
                # FIX 3: Increase max_tokens so JSON never gets cut off
                max_tokens=200
            )

            if not response or not response.choices or len(response.choices) == 0:
                raise ValueError("LLM returned no choices")

            response_text = response.choices[0].message.content
            if not response_text or not response_text.strip():
                raise ValueError("LLM returned empty response")

            response_text = response_text.strip()

            # Strip markdown code blocks if present
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()

            # Extract first JSON object from response
            json_match = re.search(r'\{[^{}]+\}', response_text)
            if json_match:
                response_text = json_match.group(0)

            action_dict = json.loads(response_text)
            action = Action(**action_dict)

            env.step(action)
            steps_taken += 1
            # FIX 4: Reset failure counter on success
            consecutive_failures = 0

        except Exception as e:
            error_msg = f"Step {step}: {e}"
            errors.append(error_msg)
            logger.debug("Auto-normalize error at step %d: %s", step, e)
            consecutive_failures += 1
            # FIX 4: Only stop if 5 consecutive failures (not on first error)
            if consecutive_failures >= 5:
                logger.debug("Too many consecutive failures, stopping")
                break
            # Otherwise continue to next step
            continue

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
