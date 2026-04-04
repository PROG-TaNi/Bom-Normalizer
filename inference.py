"""
Baseline Inference Script
Production-grade LLM-based agent for BOM normalization

CRITICAL: This file MUST be named exactly 'inference.py' and placed in project root
"""

import os
import json
import time
import requests
from openai import OpenAI


# Environment variables (Competition requirements)
API_BASE_URL = os.getenv('API_BASE_URL', 'https://router.huggingface.co/v1')
MODEL_NAME = os.getenv('MODEL_NAME', 'meta-llama/Llama-3.3-70B-Instruct')
HF_TOKEN = os.getenv('HF_TOKEN', '')  # REQUIRED by competition
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', HF_TOKEN)  # Backward compatibility
ENV_URL = os.getenv('ENV_URL', 'http://localhost:7860')  # HuggingFace Spaces port
MAX_STEPS = int(os.getenv('MAX_STEPS', '30'))


# Initialize OpenAI client (use HF_TOKEN as primary, OPENAI_API_KEY as fallback)
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN or OPENAI_API_KEY
)


SYSTEM_PROMPT = """You are an expert BOM (Bill of Materials) normalization agent for electronics manufacturing.

Your mission: Clean messy vendor names, component values, package codes, and part numbers to canonical standards.

## AVAILABLE ACTIONS

1. normalize_vendor — Standardize vendor/manufacturer name
   {"action_type": "normalize_vendor", "row_id": 1, "new_value": "Texas Instruments"}

2. normalize_value — Standardize component value with units
   {"action_type": "normalize_value", "row_id": 2, "new_value": "10000"}

3. normalize_package — Standardize package code
   {"action_type": "normalize_package", "row_id": 3, "new_value": "SOT-23"}

4. normalize_part — Standardize part number
   {"action_type": "normalize_part", "row_id": 4, "new_value": "SN74HC00N"}

5. merge_rows — Mark duplicate row (Hard task only)
   {"action_type": "merge_rows", "row_id": 5, "duplicate_row_id": 2}

6. inspect_row — Get hint about what's wrong (3 hints per episode)
   {"action_type": "inspect_row", "row_id": 1}

7. batch_normalize — Normalize all rows with same value (high risk/reward)
   {"action_type": "batch_normalize", "field": "vendor_name", "from_value": "TI", "new_value": "Texas Instruments"}

8. undo_last — Undo previous action if it was wrong
   {"action_type": "undo_last"}

9. submit — Finish episode
   {"action_type": "submit"}

## NORMALIZATION RULES

### Vendor Names (Canonical Standards)
- "TI", "T.I.", "Texas Inst.", "Texas Instruments Inc" → "Texas Instruments"
- "Murata", "MURATA", "Murata Mfg" → "Murata Manufacturing"
- "ST", "STMicro", "ST Micro" → "STMicroelectronics"
- "Vishay", "VISHAY" → "Vishay Intertechnology"
- "ON Semi", "ON Semi.", "OnSemi" → "ON Semiconductor"
- "NXP", "NXP Semi" → "NXP Semiconductors"
- "Infineon", "Infinion" (typo) → "Infineon Technologies"
- "Analog", "ADI" → "Analog Devices"
- "Maxim", "Maxim Int" → "Maxim Integrated"
- "Microchip", "MCHP" → "Microchip Technology"
- "TDK", "TDK Corp" → "TDK Corporation"
- "Samsung", "Samsung Electro" → "Samsung"
- "Panasonic", "Pana" → "Panasonic"
- "Rohm", "ROHM" → "Rohm Semiconductor"
- "Linear", "LT", "Linear Tech" → "Linear Technology"
- "Cypress", "Cypress Semi" → "Cypress Semiconductor"
- "Renesas", "Renesas Elec" → "Renesas Electronics"
- "Broadcom", "BRCM" → "Broadcom"
- "Qualcomm", "QCOM" → "Qualcomm"
- "Intel", "INTC" → "Intel"

### Component Values (Resistance/Capacitance)
Resistance (Ohms):
- "10K", "10k", "10kΩ", "10kohm" → "10000"
- "1M", "1MΩ", "1Mohm" → "1000000"
- "100", "100Ω", "100ohm" → "100"

Capacitance (Farads in scientific notation):
- "100nF", "0.1uF" → "100e-9"
- "10uF", "10µF" → "10e-6"
- "1000pF", "1nF" → "1e-9"
- "22uF" → "22e-6"
- "1uF" → "1e-6"

Voltage (Volts):
- "5V", "5.0V" → "5"
- "3.3V" → "3.3"

### Package Codes
- "SOT23", "SOT23-3", "sot 23" → "SOT-23"
- "0402M", "0402 " → "0402"
- "DIP14", "dip 14" → "DIP-14"
- "SOIC8", "SOIC-8" → "SOIC-8"
- "QFN56" → "QFN-56"
- "LQFP48" → "LQFP-48"
- "TO92", "TO 92" → "TO-92"

### Part Numbers
- Remove extra prefixes: "SN74HC00" → "SN74HC00N" (add suffix if missing)
- Standardize case: maintain manufacturer's original case

## STRATEGY

1. Start with BATCH operations for common patterns (e.g., all "TI" → "Texas Instruments")
2. Use INSPECT_ROW sparingly (only 3 hints) for ambiguous cases
3. For Hard task: identify duplicates by matching part_number + vendor after normalization
4. Use UNDO_LAST if you make a mistake
5. Normalize systematically: vendors first, then values, then packages
6. Call SUBMIT when fields_remaining reaches 0 or you're confident

## OUTPUT FORMAT

Respond with ONLY a valid JSON object. No markdown, no explanation, just JSON:
{"action_type": "normalize_vendor", "row_id": 1, "new_value": "Texas Instruments"}
"""


def wait_for_server(url: str, timeout: int = 30, interval: int = 2):
    """Wait for server to be ready"""
    print(f"Waiting for server at {url}...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/health", timeout=2)
            if response.status_code == 200:
                print("Server is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(interval)
    
    print(f"Warning: Server not responding after {timeout}s, proceeding anyway...")
    return False


def call_llm(user_content: str, retry_count: int = 3) -> str:
    """
    Call LLM API with retry logic
    
    Args:
        user_content: User message
        retry_count: Number of retries on failure
    
    Returns:
        LLM response text
    """
    for attempt in range(retry_count):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': user_content}
                ],
                temperature=0.0,  # CRITICAL: Must be 0.0 for reproducibility
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM API error (attempt {attempt + 1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                time.sleep(1)
            else:
                # Fallback action
                return '{"action_type": "submit"}'
    
    return '{"action_type": "submit"}'


def parse_action(response: str) -> dict:
    """
    Parse LLM response as action JSON with robust error handling
    
    Args:
        response: Raw LLM response
    
    Returns:
        Action dict or fallback submit action
    """
    try:
        # Remove markdown code blocks if present
        if '```json' in response:
            response = response.split('```json')[1].split('```')[0].strip()
        elif '```' in response:
            response = response.split('```')[1].split('```')[0].strip()
        
        # Remove any leading/trailing whitespace
        response = response.strip()
        
        # Parse JSON
        action = json.loads(response)
        
        # Validate required fields
        if 'action_type' not in action:
            raise ValueError("Missing action_type field")
        
        return action
    
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Raw response: {response[:200]}")
        return {'action_type': 'submit'}
    
    except Exception as e:
        print(f"Action parse error: {e}")
        return {'action_type': 'submit'}


def run_task(task_id: str) -> float:
    """
    Run agent on one task with structured logging for competition evaluation
    
    Args:
        task_id: Task identifier ('easy', 'medium', 'hard')
    
    Returns:
        Final score (0.0 to 1.0)
    """
    # [START] log - REQUIRED by competition
    print(f"[START] task={task_id} env=bom-normalizer model={MODEL_NAME}")
    
    # Track rewards for [END] log
    rewards_list = []
    
    # Reset environment
    try:
        reset_url = f"{ENV_URL}/reset?task_id={task_id}"
        response = requests.post(reset_url, timeout=10)
        response.raise_for_status()
        obs = response.json()
    except Exception as e:
        print(f"[ERROR] task={task_id} error=reset_failed message={str(e)}")
        print(f"[END] success=false steps=0 score=0.000 rewards=")
        return 0.0
    
    # Agent loop
    for step in range(obs['max_steps']):
        # Build context for LLM
        raw_rows = [r for r in obs['rows'] if r['status'] == 'raw'][:15]
        
        if not raw_rows and obs['fields_remaining'] == 0:
            user_content = "All rows normalized. Submit now."
        else:
            rows_str = json.dumps(raw_rows, indent=2)
            user_content = f"""Task: {obs['task_description']}
Step: {obs['step_count']} / {obs['max_steps']}
Fields remaining: {obs['fields_remaining']}
Hint budget: {obs.get('hint_budget', 0)}
Last action result: {obs.get('last_action_result', 'N/A')}

RAW rows (first 15):
{rows_str}

Choose your next action wisely."""
        
        # Get action from LLM
        llm_response = call_llm(user_content)
        action = parse_action(llm_response)
        
        # Execute action
        try:
            step_url = f"{ENV_URL}/step?task_id={task_id}"
            response = requests.post(step_url, json=action, timeout=10)
            response.raise_for_status()
            result = response.json()
        except Exception as e:
            print(f"[ERROR] task={task_id} step={step+1} error=step_failed message={str(e)}")
            rewards_str = ",".join(f"{r:.2f}" for r in rewards_list)
            print(f"[END] success=false steps={step+1} score=0.000 rewards={rewards_str}")
            return 0.0
        
        obs = result['observation']
        reward = result['reward']
        done = result['done']
        
        # Track reward
        rewards_list.append(reward['value'])
        
        # [STEP] log - REQUIRED by competition
        action_str = action.get('action_type', 'unknown')
        error_val = "null"
        print(f"[STEP] step={obs['step_count']} action={action_str} reward={reward['value']:.2f} done={str(done).lower()} error={error_val}")
        
        # Check if done
        if done:
            score = result['info'].get('score', 0.0)
            # [END] log - REQUIRED by competition
            rewards_str = ",".join(f"{r:.2f}" for r in rewards_list)
            success = score > 0.0
            print(f"[END] success={str(success).lower()} steps={obs['step_count']} score={score:.3f} rewards={rewards_str}")
            return score
    
    # Max steps reached without submit
    rewards_str = ",".join(f"{r:.2f}" for r in rewards_list)
    print(f"[END] success=false steps={obs['max_steps']} score=0.000 rewards={rewards_str}")
    return 0.0


def main():
    """Main entry point for inference script with structured logging"""
    # Run all three tasks
    scores = {}
    for task_id in ['easy', 'medium', 'hard']:
        score = run_task(task_id)
        scores[task_id] = score
        time.sleep(1)  # Brief pause between tasks
    
    # Print summary (not parsed by evaluator, just for humans)
    print(f"\n# Summary: easy={scores['easy']:.4f} medium={scores['medium']:.4f} hard={scores['hard']:.4f} average={sum(scores.values())/3:.4f}")
    
    # Return average score for automated evaluation
    return sum(scores.values()) / len(scores)


if __name__ == '__main__':
    main()
