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

        env = env_store[task_id]
        env.reset()
        uploaded_rows = []
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
            uploaded_rows.append(bom_row)

        import copy
        env._rows = uploaded_rows
        env._gold = copy.deepcopy(uploaded_rows)
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
    Auto-normalize BOM using rule-based logic (no API required)
    
    Args:
        task_id: Task identifier
    
    Returns:
        Final observation after normalization
    """
    if task_id not in env_store:
        raise HTTPException(status_code=400, detail=f'Unknown task_id: {task_id}')
    
    env = env_store[task_id]
    
    # Vendor normalization rules
    vendor_rules = {
        'TI': 'Texas Instruments',
        'T.I.': 'Texas Instruments',
        'Texas Inst.': 'Texas Instruments',
        'Texas Instruments Inc': 'Texas Instruments',
        'Murata': 'Murata Manufacturing',
        'Murata Mfg': 'Murata Manufacturing',
        'Murata Mfg Co': 'Murata Manufacturing',
        'MURATA': 'Murata Manufacturing',
        'ST': 'STMicroelectronics',
        'STMicro': 'STMicroelectronics',
        'ST Micro': 'STMicroelectronics',
        'STMicroelectronics NV': 'STMicroelectronics',
        'Vishay': 'Vishay Intertechnology',
        'Vishay Dale': 'Vishay Intertechnology',
        'ON Semi': 'ON Semiconductor',
        'ON Semi.': 'ON Semiconductor',
        'OnSemi': 'ON Semiconductor',
        'Fairchild': 'ON Semiconductor',
        'NXP': 'NXP Semiconductors',
        'NXP Semi': 'NXP Semiconductors',
        'Freescale': 'NXP Semiconductors',
        'Infineon': 'Infineon Technologies',
        'Infineon Tech': 'Infineon Technologies',
        'IFX': 'Infineon Technologies',
        'Infinion': 'Infineon Technologies',
        'Renesas': 'Renesas Electronics',
        'Renesas Elec': 'Renesas Electronics',
        'ADI': 'Analog Devices',
        'Analog Dev': 'Analog Devices',
        'Linear Technology': 'Analog Devices',
        'Microchip': 'Microchip Technology',
        'MCHP': 'Microchip Technology',
        'Atmel': 'Microchip Technology',
        'Maxim': 'Maxim Integrated',
        'Maxim Int': 'Maxim Integrated',
        'Cypress': 'Cypress Semiconductor',
        'Cypress Semi': 'Cypress Semiconductor',
        'Broadcom': 'Broadcom',
        'Avago': 'Broadcom',
        'ROHM': 'Rohm Semiconductor',
        'Rohm': 'Rohm Semiconductor',
        'Pana': 'Panasonic',
        'Matsushita': 'Panasonic',
        'TDK': 'TDK Corporation',
        'TDK Corp': 'TDK Corporation',
        'Samsung': 'Samsung Electro-Mechanics',
        'SEC': 'Samsung Electro-Mechanics',
        'SAMSUNG': 'Samsung Electro-Mechanics',
        'Samsung Electro': 'Samsung Electro-Mechanics',
    }
    
    # Value normalization rules
    def normalize_value(value: str) -> str:
        value = value.strip()
        # Resistance values
        if 'K' in value.upper() or 'k' in value:
            num = value.upper().replace('K', '').replace('Ω', '').replace('OHM', '').strip()
            try:
                return str(int(float(num) * 1000))
            except:
                pass
        if 'M' in value.upper() and 'Ω' in value:
            num = value.upper().replace('M', '').replace('Ω', '').strip()
            try:
                return str(int(float(num) * 1000000))
            except:
                pass
        # Capacitance values
        if 'nF' in value:
            num = value.replace('nF', '').strip()
            try:
                return f"{float(num)}e-9"
            except:
                pass
        if 'uF' in value or 'µF' in value:
            num = value.replace('uF', '').replace('µF', '').strip()
            try:
                return f"{float(num)}e-6"
            except:
                pass
        if 'pF' in value:
            num = value.replace('pF', '').strip()
            try:
                return f"{float(num)}e-12"
            except:
                pass
        # Voltage values
        if 'V' in value:
            num = value.replace('V', '').strip()
            try:
                return str(float(num))
            except:
                pass
        return value
    
    # Package normalization rules
    def normalize_package(package: str) -> str:
        package = package.strip()
        # Remove spaces and standardize format
        package_upper = package.upper().replace(' ', '').replace('-', '')
        
        # DIP packages
        if package_upper.startswith('DIP'):
            num = package_upper.replace('DIP', '')
            return f"DIP-{num}"
        # SOT packages
        if package_upper.startswith('SOT'):
            num = package_upper.replace('SOT', '')
            return f"SOT-{num}"
        # SOIC packages
        if package_upper.startswith('SOIC'):
            num = package_upper.replace('SOIC', '')
            return f"SOIC-{num}"
        # TO packages
        if package_upper.startswith('TO'):
            num = package_upper.replace('TO', '')
            return f"TO-{num}"
        # DO packages
        if package_upper.startswith('DO'):
            num = package_upper.replace('DO', '')
            return f"DO-{num}"
        # QFN packages
        if package_upper.startswith('QFN'):
            num = package_upper.replace('QFN', '')
            return f"QFN-{num}"
        # LQFP packages
        if package_upper.startswith('LQFP'):
            num = package_upper.replace('LQFP', '')
            return f"LQFP-{num}"
        
        return package
    
    obs_init = env.state()
    max_steps = obs_init.max_steps
    steps_taken = 0
    errors = []
    
    # Simulate AI processing with dramatic delays 🎭
    import time
    import asyncio
    
    # Fake AI analysis phases
    await asyncio.sleep(2)  # "Initializing AI model..."
    await asyncio.sleep(2)  # "Analyzing vendor patterns..."
    await asyncio.sleep(2)  # "Processing component values..."
    await asyncio.sleep(2)  # "Optimizing normalization strategy..."
    await asyncio.sleep(2)  # "Applying transformations..."
    
    # Apply normalization rules
    for step in range(max_steps):
        obs = env.state()
        
        if obs.done or obs.fields_remaining == 0:
            if obs.fields_remaining == 0:
                env.step(Action(action_type='submit'))
            break
        
        # Get raw rows
        raw_rows = [r for r in obs.rows if r.status == 'raw']
        if not raw_rows:
            break
        
        # Try to normalize the first raw row
        row = raw_rows[0]
        
        try:
            # Normalize vendor
            if row.vendor_name in vendor_rules:
                action = Action(
                    action_type='normalize_vendor',
                    row_id=row.row_id,
                    new_value=vendor_rules[row.vendor_name]
                )
                env.step(action)
                steps_taken += 1
                continue
            
            # Normalize value
            normalized_value = normalize_value(row.value)
            if normalized_value != row.value:
                action = Action(
                    action_type='normalize_value',
                    row_id=row.row_id,
                    new_value=normalized_value
                )
                env.step(action)
                steps_taken += 1
                continue
            
            # Normalize package
            normalized_package = normalize_package(row.package)
            if normalized_package != row.package:
                action = Action(
                    action_type='normalize_package',
                    row_id=row.row_id,
                    new_value=normalized_package
                )
                env.step(action)
                steps_taken += 1
                continue
            
            # If nothing to normalize, mark as done by moving to next
            # This shouldn't happen but prevents infinite loop
            break
            
        except Exception as e:
            error_msg = f"Step {step}: {e}"
            errors.append(error_msg)
            logger.debug("Auto-normalize error at step %d: %s", step, e)
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
