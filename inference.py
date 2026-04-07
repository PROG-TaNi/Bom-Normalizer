"""
Baseline Inference Script — BOM Normalizer (OpenEnv)

MANDATORY (competition):
- API_BASE_URL, MODEL_NAME — LLM endpoint and model id.
- HF_TOKEN — API key (Hugging Face or compatible).
- LOCAL_IMAGE_NAME — only if using from_docker_image(); this script uses HTTP ENV_URL instead.

STDOUT: only [START], [STEP], [END] lines per competition spec.
All other messages go to stderr.
"""

import json
import os
import sys
import time
from typing import List, Optional

import requests
from openai import OpenAI

# Defaults only for API_BASE_URL and MODEL_NAME (competition rule). No default for HF_TOKEN.
API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.getenv("MODEL_NAME") or "meta-llama/Llama-3.3-70B-Instruct"
HF_TOKEN = os.getenv("HF_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Optional — if you use from_docker_image() (this script uses HTTP ENV_URL instead)
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")
IMAGE_NAME = os.getenv("IMAGE_NAME")
ENV_URL = os.getenv("ENV_URL", "http://localhost:7860")

BENCHMARK = "bom-normalizer"
SUCCESS_SCORE_THRESHOLD = 0.1

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN or OPENAI_API_KEY or "",
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
- "Samsung", "Samsung Electro", "SEC", "SAMSUNG" → "Samsung Electro-Mechanics"
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


def _err(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


def wait_for_server(url: str, timeout: int = 60, interval: int = 2) -> None:
    _err(f"Waiting for server at {url}...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{url}/health", timeout=2)
            if r.status_code == 200:
                _err("Server is ready!")
                return
        except requests.exceptions.RequestException:
            pass
        time.sleep(interval)
    _err(f"Warning: server not responding after {timeout}s, proceeding anyway...")


def call_llm(user_content: str, retry_count: int = 3) -> str:
    for attempt in range(retry_count):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.0,
                max_tokens=200,
            )
            text = (response.choices[0].message.content or "").strip()
            return text
        except Exception as e:
            _err(f"LLM API error (attempt {attempt + 1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                time.sleep(1)
    return '{"action_type": "submit"}'


def parse_action(response: str) -> dict:
    try:
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
        response = response.strip()
        action = json.loads(response)
        if "action_type" not in action:
            raise ValueError("Missing action_type field")
        return action
    except json.JSONDecodeError as e:
        _err(f"JSON parse error: {e}")
        _err(f"Raw response: {response[:200]}")
        return {"action_type": "submit"}
    except Exception as e:
        _err(f"Action parse error: {e}")
        return {"action_type": "submit"}


def run_task(task_id: str) -> float:
    rewards_list: List[float] = []
    steps_taken = 0
    final_score = 0.0
    success = False

    log_start(task_id, BENCHMARK, MODEL_NAME)

    try:
        try:
            response = requests.post(
                f"{ENV_URL}/reset?task_id={task_id}", timeout=30
            )
            response.raise_for_status()
            obs = response.json()
        except Exception as e:
            _err(f"reset failed: {e}")
            obs = None

        if obs is not None:
            max_steps = int(obs["max_steps"])
            for _ in range(max_steps):
                raw_rows = [r for r in obs["rows"] if r["status"] == "raw"][:15]

                if not raw_rows and obs["fields_remaining"] == 0:
                    user_content = "All rows normalized. Submit now."
                else:
                    rows_str = json.dumps(raw_rows, indent=2)
                    user_content = (
                        f"Task: {obs['task_description']}\n"
                        f"Step: {obs['step_count']} / {obs['max_steps']}\n"
                        f"Fields remaining: {obs['fields_remaining']}\n"
                        f"Hint budget: {obs.get('hint_budget', 0)}\n"
                        f"Last action result: {obs.get('last_action_result', 'N/A')}\n\n"
                        f"RAW rows (first 15):\n{rows_str}\n\n"
                        "Choose your next action wisely."
                    )

                llm_response = call_llm(user_content)
                action = parse_action(llm_response)

                try:
                    response = requests.post(
                        f"{ENV_URL}/step?task_id={task_id}",
                        json=action,
                        timeout=30,
                    )
                    response.raise_for_status()
                    result = response.json()
                except Exception as e:
                    _err(f"step failed: {e}")
                    break

                obs = result["observation"]
                reward = result["reward"]
                done = result["done"]
                rewards_list.append(float(reward["value"]))

                action_str = action.get("action_type", "unknown")
                step_num = int(obs["step_count"])
                last_res = obs.get("last_action_result")
                err_str: Optional[str] = None
                if last_res and (
                    last_res.startswith("Invalid")
                    or "No hints remaining" in last_res
                    or "No actions to undo" in last_res
                ):
                    err_str = last_res

                log_step(
                    step_num,
                    action_str,
                    float(reward["value"]),
                    bool(done),
                    err_str,
                )
                steps_taken = step_num

                if done:
                    final_score = float(result["info"].get("score", 0.0))
                    final_score = min(max(final_score, 0.0), 1.0)
                    success = final_score >= SUCCESS_SCORE_THRESHOLD
                    break
            else:
                steps_taken = max_steps
                final_score = 0.0
                success = False

    finally:
        log_end(success, steps_taken, final_score, rewards_list)

    return final_score


def main() -> None:
    wait_for_server(ENV_URL, timeout=60)
    scores = {}
    for task_id in ("easy", "medium", "hard"):
        scores[task_id] = run_task(task_id)
        time.sleep(1)
    _err(
        f"# Summary: easy={scores['easy']:.4f} medium={scores['medium']:.4f} "
        f"hard={scores['hard']:.4f} average={sum(scores.values()) / 3:.4f}"
    )


if __name__ == "__main__":
    main()
