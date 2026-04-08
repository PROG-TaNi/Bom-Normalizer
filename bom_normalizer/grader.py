"""
Grader Module
Deterministic scoring functions for each task
"""

import re
from typing import List
from .models import BOMRow, RowStatus


def _levenshtein_similarity(s1: str, s2: str) -> float:
    """
    Calculate Levenshtein similarity between two strings
    Returns value in [0.0, 1.0] where 1.0 is identical
    """
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    
    # Levenshtein distance calculation
    len1, len2 = len(s1), len(s2)
    if len1 < len2:
        s1, s2 = s2, s1
        len1, len2 = len2, len1
    
    current_row = range(len2 + 1)
    for i in range(1, len1 + 1):
        previous_row = current_row
        current_row = [i] + [0] * len2
        for j in range(1, len2 + 1):
            add = previous_row[j] + 1
            delete = current_row[j - 1] + 1
            change = previous_row[j - 1]
            if s1[i - 1] != s2[j - 1]:
                change += 1
            current_row[j] = min(add, delete, change)
    
    distance = current_row[len2]
    max_len = max(len1, len2)
    return 1.0 - (distance / max_len)


def _normalize_to_base_value(value: str) -> tuple:
    """
    Normalize a value with unit to base unit
    Returns (numeric_value, base_unit) or (None, None) if invalid
    
    Examples:
        "10uF" -> (10.0, "F")
        "1000pF" -> (0.001, "F")  # 1000pF = 0.001uF = 0.000001F
        "2.2kΩ" -> (2200.0, "Ω")
        "100mH" -> (0.1, "H")
    """
    if not value:
        return (None, None)
    
    # Remove spaces
    value = value.strip()
    
    # Extract numeric part and unit part
    match = re.match(r'^([\d.]+)\s*([a-zA-ZΩμ]+)$', value)
    if not match:
        return (None, None)
    
    num_str, unit_str = match.groups()
    try:
        num = float(num_str)
    except ValueError:
        return (None, None)
    
    # Unit conversion multipliers
    multipliers = {
        'p': 1e-12,  # pico
        'n': 1e-9,   # nano
        'u': 1e-6,   # micro
        'μ': 1e-6,   # micro (Greek)
        'm': 1e-3,   # milli
        'k': 1e3,    # kilo
        'M': 1e6,    # mega
        'G': 1e9,    # giga
    }
    
    # Determine base unit and multiplier
    if len(unit_str) > 1 and unit_str[0] in multipliers:
        multiplier = multipliers[unit_str[0]]
        base_unit = unit_str[1:]
    else:
        multiplier = 1.0
        base_unit = unit_str
    
    # Normalize base unit variations
    base_unit_map = {
        'F': 'F',   # Farad
        'H': 'H',   # Henry
        'Ω': 'Ω',   # Ohm
        'ohm': 'Ω',
        'OHM': 'Ω',
        'V': 'V',   # Volt
        'A': 'A',   # Ampere
        'W': 'W',   # Watt
    }
    base_unit = base_unit_map.get(base_unit, base_unit)
    
    return (num * multiplier, base_unit)


def _are_values_equivalent(v1: str, v2: str, tolerance: float = 0.01) -> bool:
    """
    Check if two values are equivalent considering unit conversions
    
    Args:
        v1, v2: Value strings (e.g., "10uF", "0.01mF")
        tolerance: Relative tolerance for numeric comparison (default 1%)
    
    Returns:
        True if values are equivalent within tolerance
    """
    if v1 == v2:
        return True
    
    num1, unit1 = _normalize_to_base_value(v1)
    num2, unit2 = _normalize_to_base_value(v2)
    
    if num1 is None or num2 is None:
        return False
    
    if unit1 != unit2:
        return False
    
    # Check if values are within tolerance
    if num1 == 0 and num2 == 0:
        return True
    
    max_val = max(abs(num1), abs(num2))
    if max_val == 0:
        return True
    
    relative_diff = abs(num1 - num2) / max_val
    return relative_diff <= tolerance


def _normalize_package_string(package: str) -> str:
    """
    Normalize package string for comparison
    Handles case variations and common abbreviations
    
    Examples:
        "smd-0805" -> "0805"
        "SMD 0805" -> "0805"
        "through-hole" -> "TH"
        "SOIC-8" -> "SOIC8"
    """
    if not package:
        return ""
    
    # Convert to uppercase and remove spaces/dashes
    normalized = package.upper().replace(" ", "").replace("-", "")
    
    # Common package mappings
    mappings = {
        "THROUGHHOLE": "TH",
        "SURFACEMOUNT": "SMD",
        "SURFACEMOUNTDEVICE": "SMD",
    }
    
    for key, value in mappings.items():
        if key in normalized:
            normalized = normalized.replace(key, value)
    
    return normalized


def _grade_easy(rows: List[BOMRow], gold: List[BOMRow]) -> float:
    """
    Grade Easy task: vendor name normalization with partial credit
    
    Scoring:
    - 1.0: Exact match
    - 0.8: Case-insensitive match
    - 0.5: Substring match (one contains the other)
    - 0.3: High similarity (Levenshtein > 0.7)
    - 0.0: No match
    """
    if not gold:
        return 0.0
    
    total_score = 0.0
    for r, g in zip(rows, gold):
        r_vendor = r.vendor_name or ""
        g_vendor = g.vendor_name or ""
        
        if r_vendor == g_vendor:
            # Exact match
            total_score += 1.0
        elif r_vendor.lower() == g_vendor.lower():
            # Case-insensitive match
            total_score += 0.8
        elif r_vendor.lower() in g_vendor.lower() or g_vendor.lower() in r_vendor.lower():
            # Substring match
            total_score += 0.5
        else:
            # Check similarity
            similarity = _levenshtein_similarity(r_vendor.lower(), g_vendor.lower())
            if similarity > 0.7:
                total_score += 0.3
            # else: 0.0
    
    return float(max(0.0001, min(0.9999, round(total_score / len(gold), 4))))


def _grade_medium(rows: List[BOMRow], gold: List[BOMRow]) -> float:
    """
    Grade Medium task: vendor + value + package normalization with partial credit
    
    Scoring per field:
    - Vendor: Same as easy task (1.0/0.8/0.5/0.3/0.0)
    - Value: 1.0 for equivalent values (unit conversion), 0.0 otherwise
    - Package: 1.0 for normalized match, 0.5 for substring, 0.0 otherwise
    """
    if not gold:
        return 0.0
    
    total_score = 0.0
    total_fields = len(gold) * 3
    
    for r, g in zip(rows, gold):
        # Grade vendor (same as easy task)
        r_vendor = r.vendor_name or ""
        g_vendor = g.vendor_name or ""
        
        if r_vendor == g_vendor:
            total_score += 1.0
        elif r_vendor.lower() == g_vendor.lower():
            total_score += 0.8
        elif r_vendor.lower() in g_vendor.lower() or g_vendor.lower() in r_vendor.lower():
            total_score += 0.5
        else:
            similarity = _levenshtein_similarity(r_vendor.lower(), g_vendor.lower())
            if similarity > 0.7:
                total_score += 0.3
        
        # Grade value (with unit equivalence)
        r_value = r.value or ""
        g_value = g.value or ""
        
        if r_value == g_value:
            total_score += 1.0
        elif _are_values_equivalent(r_value, g_value):
            total_score += 1.0
        # else: 0.0
        
        # Grade package (with normalization)
        r_package = r.package or ""
        g_package = g.package or ""
        
        r_norm = _normalize_package_string(r_package)
        g_norm = _normalize_package_string(g_package)
        
        if r_norm == g_norm:
            total_score += 1.0
        elif r_norm in g_norm or g_norm in r_norm:
            total_score += 0.5
        # else: 0.0
    
    return float(max(0.0001, min(0.9999, round(total_score / total_fields, 4))))


def _grade_hard(rows: List[BOMRow], gold: List[BOMRow]) -> float:
    """
    Grade Hard task: full normalization + deduplication
    
    Components:
    - Field normalization (50%)
    - Duplicate detection (30%)
    - Quantity aggregation (20%)
    """
    if not gold:
        return 0.0
    
    # Component 1: Field normalization (50%)
    non_dup_rows = [r for r in rows if r.status != RowStatus.MERGED]
    non_dup_gold = [g for g in gold if not g.merged_into]
    
    if non_dup_gold:
        field_score = _grade_medium(non_dup_rows, non_dup_gold)
    else:
        field_score = 0.0
    
    # Component 2: Duplicate detection (30%)
    gold_pairs = {(g.row_id, g.merged_into) for g in gold if g.merged_into}
    found_pairs = {(r.row_id, r.merged_into) for r in rows if r.status == RowStatus.MERGED}
    
    if gold_pairs:
        dup_score = len(gold_pairs & found_pairs) / len(gold_pairs)
    else:
        dup_score = 1.0  # No duplicates to find
    
    # Component 3: Quantity aggregation (20%)
    qty_score = _grade_quantities(rows, gold)
    
    # Weighted combination
    final_score = field_score * 0.5 + dup_score * 0.3 + qty_score * 0.2
    
    return float(max(0.0001, min(0.9999, round(final_score, 4))))


def _grade_quantities(rows: List[BOMRow], gold: List[BOMRow]) -> float:
    """Grade quantity aggregation accuracy"""
    # Simplified: check if quantities match for non-merged rows
    if not gold:
        return 0.0
    
    correct = 0
    total = 0
    
    for r, g in zip(rows, gold):
        if r.status != RowStatus.MERGED and not g.merged_into:
            total += 1
            if r.quantity == g.quantity:
                correct += 1
    
    return correct / total if total > 0 else 0.0


def grade(rows: List[BOMRow], gold: List[BOMRow], task_id: str) -> float:
    """
    Grade agent performance
    
    Args:
        rows: Agent's final BOM rows
        gold: Gold standard BOM rows
        task_id: Task identifier ('easy', 'medium', 'hard')
    
    Returns:
        Score in [0.0, 1.0]
    """
    if task_id == 'easy':
        return _grade_easy(rows, gold)
    elif task_id == 'medium':
        return _grade_medium(rows, gold)
    elif task_id == 'hard':
        return _grade_hard(rows, gold)
    else:
        return 0.0001  # Clamped minimum
