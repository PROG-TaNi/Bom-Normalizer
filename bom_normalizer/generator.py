"""
BOM Data Generator
Generates deterministic messy and gold BOMs from seed
"""

import random
import json
import copy
from pathlib import Path
from typing import List, Tuple
from .models import BOMRow, RowStatus


# Canonical base BOM (50 entries)
CANONICAL_BOM = [
    {'vendor': 'Texas Instruments', 'part': 'SN74HC00N', 'value': '5', 'package': 'DIP-14', 'qty': 10},
    {'vendor': 'Murata Manufacturing', 'part': 'GRM188R71H104KA93D', 'value': '100e-9', 'package': '0402', 'qty': 100},
    {'vendor': 'Vishay Intertechnology', 'part': 'CRCW040210K0FKED', 'value': '10000', 'package': '0402', 'qty': 50},
    {'vendor': 'STMicroelectronics', 'part': 'LM358N', 'value': '5', 'package': 'DIP-8', 'qty': 5},
    {'vendor': 'ON Semiconductor', 'part': '1N4148', 'value': '100', 'package': 'DO-35', 'qty': 200},
    {'vendor': 'NXP Semiconductors', 'part': 'BC547', 'value': '45', 'package': 'TO-92', 'qty': 30},
    {'vendor': 'Infineon Technologies', 'part': '2N2222', 'value': '40', 'package': 'TO-18', 'qty': 25},
    {'vendor': 'Texas Instruments', 'part': 'LM7805', 'value': '5', 'package': 'TO-220', 'qty': 10},
    {'vendor': 'Texas Instruments', 'part': 'NE555', 'value': '5', 'package': 'DIP-8', 'qty': 15},
    {'vendor': 'Microchip Technology', 'part': 'ATmega328P', 'value': '5', 'package': 'DIP-28', 'qty': 5},
    {'vendor': 'Analog Devices', 'part': 'AD8221', 'value': '5', 'package': 'SOIC-8', 'qty': 8},
    {'vendor': 'Maxim Integrated', 'part': 'MAX232', 'value': '5', 'package': 'DIP-16', 'qty': 12},
    {'vendor': 'Cypress Semiconductor', 'part': 'CY7C68013A', 'value': '3.3', 'package': 'QFN-56', 'qty': 3},
    {'vendor': 'Renesas Electronics', 'part': 'R5F100LEA', 'value': '3.3', 'package': 'LQFP-48', 'qty': 4},
    {'vendor': 'Broadcom', 'part': 'BCM2837', 'value': '3.3', 'package': 'BGA-400', 'qty': 2},
    {'vendor': 'Murata Manufacturing', 'part': 'GRM155R71C104KA88D', 'value': '100e-9', 'package': '0402', 'qty': 150},
    {'vendor': 'TDK Corporation', 'part': 'C1608X7R1H104K', 'value': '100e-9', 'package': '0603', 'qty': 80},
    {'vendor': 'Samsung', 'part': 'CL10A106KP8NNNC', 'value': '10e-6', 'package': '0603', 'qty': 60},
    {'vendor': 'Panasonic', 'part': 'ERJ-3EKF1002V', 'value': '10000', 'package': '0603', 'qty': 100},
    {'vendor': 'Rohm Semiconductor', 'part': 'MCR03EZPFX1002', 'value': '10000', 'package': '0603', 'qty': 75},
    {'vendor': 'Vishay Intertechnology', 'part': 'CRCW06031K00FKEA', 'value': '1000', 'package': '0603', 'qty': 90},
    {'vendor': 'Texas Instruments', 'part': 'TPS54331', 'value': '3.3', 'package': 'SOIC-8', 'qty': 6},
    {'vendor': 'Linear Technology', 'part': 'LT1763', 'value': '3.3', 'package': 'SOT-23-5', 'qty': 8},
    {'vendor': 'STMicroelectronics', 'part': 'STM32F103C8T6', 'value': '3.3', 'package': 'LQFP-48', 'qty': 5},
    {'vendor': 'NXP Semiconductors', 'part': 'LPC1768', 'value': '3.3', 'package': 'LQFP-100', 'qty': 3},
    {'vendor': 'Infineon Technologies', 'part': 'XMC4500', 'value': '3.3', 'package': 'LQFP-144', 'qty': 2},
    {'vendor': 'ON Semiconductor', 'part': 'NCP1117', 'value': '3.3', 'package': 'SOT-223', 'qty': 10},
    {'vendor': 'Analog Devices', 'part': 'AD7606', 'value': '5', 'package': 'TQFP-64', 'qty': 4},
    {'vendor': 'Maxim Integrated', 'part': 'MAX3232', 'value': '3.3', 'package': 'SOIC-16', 'qty': 7},
    {'vendor': 'Microchip Technology', 'part': 'PIC18F4550', 'value': '5', 'package': 'DIP-40', 'qty': 6},
    {'vendor': 'Texas Instruments', 'part': 'TLC555', 'value': '5', 'package': 'SOIC-8', 'qty': 12},
    {'vendor': 'Murata Manufacturing', 'part': 'GRM21BR71H105KA12L', 'value': '1e-6', 'package': '0805', 'qty': 50},
    {'vendor': 'TDK Corporation', 'part': 'C2012X7R1H105K', 'value': '1e-6', 'package': '0805', 'qty': 45},
    {'vendor': 'Samsung', 'part': 'CL21A226MQQNNNE', 'value': '22e-6', 'package': '0805', 'qty': 30},
    {'vendor': 'Panasonic', 'part': 'ERJ-6ENF1003V', 'value': '100000', 'package': '0805', 'qty': 60},
    {'vendor': 'Rohm Semiconductor', 'part': 'MCR10EZPFX1003', 'value': '100000', 'package': '0805', 'qty': 55},
    {'vendor': 'Vishay Intertechnology', 'part': 'CRCW080510K0FKEA', 'value': '10000', 'package': '0805', 'qty': 70},
    {'vendor': 'STMicroelectronics', 'part': 'L7805CV', 'value': '5', 'package': 'TO-220', 'qty': 8},
    {'vendor': 'ON Semiconductor', 'part': 'LM317T', 'value': '1.25', 'package': 'TO-220', 'qty': 6},
    {'vendor': 'Texas Instruments', 'part': 'TL071', 'value': '5', 'package': 'DIP-8', 'qty': 10},
    {'vendor': 'Analog Devices', 'part': 'OP07', 'value': '5', 'package': 'DIP-8', 'qty': 8},
    {'vendor': 'Maxim Integrated', 'part': 'MAX485', 'value': '5', 'package': 'DIP-8', 'qty': 15},
    {'vendor': 'NXP Semiconductors', 'part': 'TJA1050', 'value': '5', 'package': 'SOIC-8', 'qty': 12},
    {'vendor': 'Infineon Technologies', 'part': 'TLE4905L', 'value': '5', 'package': 'SOT-23', 'qty': 20},
    {'vendor': 'Microchip Technology', 'part': 'MCP2551', 'value': '5', 'package': 'DIP-8', 'qty': 10},
    {'vendor': 'Cypress Semiconductor', 'part': 'CY8C4245AXI', 'value': '3.3', 'package': 'TQFP-44', 'qty': 5},
    {'vendor': 'Renesas Electronics', 'part': 'R7FA4M1AB3CFM', 'value': '3.3', 'package': 'LQFP-64', 'qty': 4},
    {'vendor': 'Broadcom', 'part': 'BCM43438', 'value': '3.3', 'package': 'WLCSP-37', 'qty': 3},
    {'vendor': 'Qualcomm', 'part': 'QCA9377', 'value': '3.3', 'package': 'BGA-88', 'qty': 2},
    {'vendor': 'Intel', 'part': 'i210', 'value': '3.3', 'package': 'BGA-196', 'qty': 1}
]


def _load_vendor_aliases() -> dict:
    """Load vendor alias mappings"""
    data_path = Path(__file__).parent.parent / 'data' / 'vendor_aliases.json'
    with open(data_path, 'r') as f:
        return json.load(f)


def _load_unit_variants() -> dict:
    """Load unit variant mappings"""
    data_path = Path(__file__).parent.parent / 'data' / 'unit_variants.json'
    with open(data_path, 'r') as f:
        return json.load(f)


def _load_part_numbers() -> dict:
    """Load part number mappings"""
    data_path = Path(__file__).parent.parent / 'data' / 'part_numbers.json'
    with open(data_path, 'r') as f:
        return json.load(f)


def _corrupt_vendor(vendor: str, rng: random.Random) -> str:
    """Corrupt vendor name with alias"""
    vendor_aliases = _load_vendor_aliases()
    if vendor in vendor_aliases and vendor_aliases[vendor]:
        return rng.choice(vendor_aliases[vendor])
    return vendor


def _corrupt_value(value: str, rng: random.Random) -> str:
    """Corrupt value with unit variants"""
    try:
        num_val = float(value.replace('e-', 'E-'))
        
        # Resistance values
        if num_val >= 1000 and num_val < 1000000:
            k_val = num_val / 1000
            variants = [f"{k_val}K", f"{k_val}k", f"{k_val}kΩ", f"{k_val}kohm"]
            return rng.choice(variants)
        elif num_val >= 1000000:
            m_val = num_val / 1000000
            variants = [f"{m_val}M", f"{m_val}MΩ", f"{m_val}Mohm"]
            return rng.choice(variants)
        
        # Capacitance values (scientific notation)
        if 'e-' in value.lower():
            exp = value.lower().split('e-')[1]
            coef = value.lower().split('e-')[0]
            if exp == '9':
                variants = [f"{coef}nF", f"{float(coef)*1000}pF"]
                return rng.choice(variants)
            elif exp == '6':
                variants = [f"{coef}uF", f"{coef}µF", f"{float(coef)*1000}nF"]
                return rng.choice(variants)
        
        return value
    except:
        return value


def _corrupt_package(package: str, rng: random.Random) -> str:
    """Corrupt package code"""
    part_data = _load_part_numbers()
    package_variants = part_data.get('package_variants', {})
    
    if package in package_variants and package_variants[package]:
        return rng.choice(package_variants[package])
    
    # Generic corruptions
    if '-' in package:
        return package.replace('-', '')
    else:
        parts = [package[i:i+3] for i in range(0, len(package), 3)]
        return '-'.join(parts) if len(parts) > 1 else package
    
    return package


def _corrupt_part(part: str, rng: random.Random) -> str:
    """Corrupt part number"""
    part_data = _load_part_numbers()
    canonical_parts = part_data.get('canonical_parts', {})
    
    if part in canonical_parts and canonical_parts[part]:
        return rng.choice(canonical_parts[part])
    
    # Generic corruptions
    if rng.random() < 0.3:
        return part.replace('SN', '').replace('N', '')
    
    return part


def _corrupt_row(row: BOMRow, rng: random.Random, difficulty: str) -> BOMRow:
    """Apply corruptions based on difficulty"""
    corrupted = copy.deepcopy(row)
    
    # Easy: vendor only
    if difficulty == 'easy':
        corrupted.vendor_name = _corrupt_vendor(row.vendor_name, rng)
    
    # Medium: vendor + value + package
    elif difficulty == 'medium':
        corrupted.vendor_name = _corrupt_vendor(row.vendor_name, rng)
        corrupted.value = _corrupt_value(row.value, rng)
        corrupted.package = _corrupt_package(row.package, rng)
    
    # Hard: all fields
    elif difficulty == 'hard':
        corrupted.vendor_name = _corrupt_vendor(row.vendor_name, rng)
        corrupted.value = _corrupt_value(row.value, rng)
        corrupted.package = _corrupt_package(row.package, rng)
        corrupted.part_number = _corrupt_part(row.part_number, rng)
    
    return corrupted


def _inject_duplicates(rows: List[BOMRow], rng: random.Random, n: int = 40) -> List[BOMRow]:
    """Inject n duplicate pairs for Hard task"""
    result = list(rows)
    
    for _ in range(n):
        if len(result) < 2:
            break
        
        # Pick a random row to duplicate
        idx = rng.randint(0, len(result) - 1)
        original = result[idx]
        
        # Create duplicate with different corruption
        duplicate = copy.deepcopy(original)
        duplicate.row_id = len(result) + 1
        duplicate.quantity = rng.randint(1, 10)
        
        # Apply different corruptions
        duplicate.vendor_name = _corrupt_vendor(original.vendor_name, rng)
        duplicate.part_number = _corrupt_part(original.part_number, rng)
        
        result.append(duplicate)
    
    # Reassign row IDs
    for i, row in enumerate(result):
        row.row_id = i + 1
    
    return result


def _inject_edge_cases(rows: List[BOMRow], rng: random.Random) -> List[BOMRow]:
    """
    Inject 10 edge case rows to make Hard task genuinely hard
    
    Edge cases include:
    - Ambiguous vendor names (abbreviations that could match multiple vendors)
    - Missing or empty fields
    - Conflicting unit representations (1000pF vs 1nF)
    - Near-duplicates with subtle differences
    - Invalid/corrupted data
    """
    edge_cases = [
        # 1. Ambiguous vendor - "TI" could be Texas Instruments or others
        BOMRow(
            row_id=len(rows) + 1,
            vendor_name="TI",
            part_number="SN74HC00",
            value="5V",
            package="DIP14",
            quantity=10,
            status=RowStatus.RAW
        ),
        # 2. Missing vendor name
        BOMRow(
            row_id=len(rows) + 2,
            vendor_name="",
            part_number="GRM188R71H104KA93D",
            value="100nF",
            package="0402",
            quantity=100,
            status=RowStatus.RAW
        ),
        # 3. Conflicting units - 1000pF = 1nF
        BOMRow(
            row_id=len(rows) + 3,
            vendor_name="Murata",
            part_number="GRM188R71H104KA93D",
            value="1000pF",
            package="0402",
            quantity=50,
            status=RowStatus.RAW
        ),
        # 4. Near-duplicate with typo in part number
        BOMRow(
            row_id=len(rows) + 4,
            vendor_name="Texas Inst",
            part_number="SN74HC00N",
            value="5",
            package="DIP-14",
            quantity=5,
            status=RowStatus.RAW
        ),
        # 5. Mixed case and spacing in package
        BOMRow(
            row_id=len(rows) + 5,
            vendor_name="STMicro",
            part_number="LM358N",
            value="5",
            package="dip 8",
            quantity=8,
            status=RowStatus.RAW
        ),
        # 6. Vendor with extra punctuation
        BOMRow(
            row_id=len(rows) + 6,
            vendor_name="ON Semi.",
            part_number="1N4148",
            value="100V",
            package="DO35",
            quantity=150,
            status=RowStatus.RAW
        ),
        # 7. Value with inconsistent notation
        BOMRow(
            row_id=len(rows) + 7,
            vendor_name="Vishay",
            part_number="CRCW040210K0FKED",
            value="10K",
            package="0402",
            quantity=75,
            status=RowStatus.RAW
        ),
        # 8. Duplicate with different quantity (should merge)
        BOMRow(
            row_id=len(rows) + 8,
            vendor_name="Texas Instruments",
            part_number="SN74HC00N",
            value="5",
            package="DIP-14",
            quantity=20,
            status=RowStatus.RAW
        ),
        # 9. Package with unusual formatting
        BOMRow(
            row_id=len(rows) + 9,
            vendor_name="NXP",
            part_number="BC547",
            value="45",
            package="TO92",
            quantity=25,
            status=RowStatus.RAW
        ),
        # 10. Vendor with common misspelling
        BOMRow(
            row_id=len(rows) + 10,
            vendor_name="Infinion",  # Should be Infineon
            part_number="2N2222",
            value="40",
            package="TO-18",
            quantity=30,
            status=RowStatus.RAW
        ),
    ]
    
    result = list(rows) + edge_cases
    
    # Reassign row IDs
    for i, row in enumerate(result):
        row.row_id = i + 1
    
    return result


def _row_count(difficulty: str) -> int:
    """Get row count for difficulty"""
    return {'easy': 10, 'medium': 50, 'hard': 50}[difficulty]  # Hard will grow to ~100 with duplicates+edges


def generate_bom(seed: int, difficulty: str) -> Tuple[List[BOMRow], List[BOMRow]]:
    """
    Generate messy and gold BOMs from seed
    
    Args:
        seed: Random seed for deterministic generation
        difficulty: 'easy', 'medium', or 'hard'
    
    Returns:
        (messy_rows, gold_rows) tuple
    """
    rng = random.Random(seed)
    
    # Select subset of canonical BOM
    count = _row_count(difficulty)
    base = CANONICAL_BOM[:count]
    
    # Create gold BOM (canonical)
    gold = [
        BOMRow(
            row_id=i + 1,
            vendor_name=row['vendor'],
            part_number=row['part'],
            value=row['value'],
            package=row['package'],
            quantity=row['qty'],
            status=RowStatus.NORMALIZED
        )
        for i, row in enumerate(base)
    ]
    
    # Create messy BOM (corrupted)
    messy = [_corrupt_row(row, rng, difficulty) for row in copy.deepcopy(gold)]
    
    # Reset status to RAW
    for row in messy:
        row.status = RowStatus.RAW
    
    # Inject duplicates for Hard task
    if difficulty == 'hard':
        messy = _inject_duplicates(messy, rng, n=40)
        # Inject edge cases to make it genuinely hard
        messy = _inject_edge_cases(messy, rng)
        # Update gold to match (mark duplicates)
        # For simplicity, we'll handle this in grader
    
    return messy, gold
