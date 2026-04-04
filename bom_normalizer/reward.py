"""
Reward Function
Dense per-step rewards for agent feedback
"""

from typing import List, Tuple
from .models import Action, ActionType, BOMRow


def _calculate_string_similarity(s1: str, s2: str) -> float:
    """
    Calculate similarity between two strings using Levenshtein distance
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


def _numeric_close(val1: str, val2: str, tolerance: float = 0.01) -> bool:
    """Check if two numeric values are within tolerance"""
    try:
        num1 = float(val1.replace('e-', 'E-'))
        num2 = float(val2.replace('e-', 'E-'))
        return abs(num1 - num2) / max(abs(num2), 1e-10) < tolerance
    except:
        return False


def _is_true_duplicate(row_id: int, dup_id: int, gold: List[BOMRow]) -> bool:
    """Check if two rows are true duplicates in gold standard"""
    # For now, simplified check
    # In full implementation, would check gold duplicate mappings
    return False  # Placeholder


def compute_reward(action: Action, rows: List[BOMRow], gold: List[BOMRow]) -> Tuple[float, str]:
    """
    Compute reward for an action
    
    Args:
        action: Action taken by agent
        rows: Current BOM rows
        gold: Gold standard BOM rows
    
    Returns:
        (reward_value, reason) tuple
    """
    
    # SUBMIT action
    if action.action_type == ActionType.SUBMIT:
        return 0.0, "Episode submitted"
    
    # Validate row_id
    if action.row_id is None or action.row_id < 1 or action.row_id > len(rows):
        return -0.05, "Invalid row_id"
    
    row_idx = action.row_id - 1
    current_row = rows[row_idx]
    
    # Find corresponding gold row
    if row_idx >= len(gold):
        return -0.05, "Row not in gold standard"
    
    gold_row = gold[row_idx]
    
    # NORMALIZE actions
    if action.action_type in [
        ActionType.NORMALIZE_VENDOR,
        ActionType.NORMALIZE_VALUE,
        ActionType.NORMALIZE_PACKAGE,
        ActionType.NORMALIZE_PART
    ]:
        if action.new_value is None:
            return -0.05, "Missing new_value for normalize action"
        
        # Determine field being normalized
        field_map = {
            ActionType.NORMALIZE_VENDOR: ('vendor_name', 'vendor_name'),
            ActionType.NORMALIZE_VALUE: ('value', 'value'),
            ActionType.NORMALIZE_PACKAGE: ('package', 'package'),
            ActionType.NORMALIZE_PART: ('part_number', 'part_number')
        }
        
        current_field, gold_field = field_map[action.action_type]
        current_val = getattr(current_row, current_field)
        gold_val = getattr(gold_row, gold_field)
        new_val = action.new_value
        
        # Check if corrupting a correct field
        if current_val == gold_val and new_val != gold_val:
            return -0.15, f"Corrupted correct {current_field}"
        
        # Check if already correct (no change needed)
        if current_val == gold_val and new_val == gold_val:
            return 0.02, f"Field already correct (no change needed)"
        
        # TIER 1: Perfect match (1.0 similarity)
        if new_val == gold_val:
            return 0.30, f"Perfect {current_field} normalization"
        
        # TIER 2: Case-insensitive match (0.9 similarity)
        if new_val.lower() == gold_val.lower():
            return 0.25, f"Correct {current_field} (case mismatch)"
        
        # TIER 3: Substring match (one contains the other)
        if new_val.lower() in gold_val.lower() or gold_val.lower() in new_val.lower():
            return 0.15, f"Partial {current_field} match (substring)"
        
        # TIER 4: High similarity (Levenshtein > 0.7)
        similarity = _calculate_string_similarity(new_val.lower(), gold_val.lower())
        if similarity > 0.7:
            return 0.10, f"Similar {current_field} (similarity: {similarity:.2f})"
        
        # TIER 5: Moderate similarity (Levenshtein > 0.5)
        if similarity > 0.5:
            return 0.05, f"Somewhat similar {current_field} (similarity: {similarity:.2f})"
        
        # TIER 6: Numeric close (for values)
        if action.action_type == ActionType.NORMALIZE_VALUE:
            if _numeric_close(new_val, gold_val):
                return 0.20, f"Numerically equivalent {current_field}"
        
        # TIER 7: Wrong but not penalized (low similarity)
        if similarity > 0.3:
            return 0.0, f"Incorrect {current_field} (low similarity: {similarity:.2f})"
        
        # TIER 8: Very wrong - small penalty
        return -0.05, f"Very incorrect {current_field} normalization"
    
    # MERGE_ROWS action
    if action.action_type == ActionType.MERGE_ROWS:
        if action.duplicate_row_id is None:
            return -0.05, "Missing duplicate_row_id for merge action"
        
        if _is_true_duplicate(action.row_id, action.duplicate_row_id, gold):
            return 0.15, "Correct duplicate pair detected"
        else:
            return -0.05, "Incorrect duplicate pair"
    
    # FLAG_ANOMALY action
    if action.action_type == ActionType.FLAG_ANOMALY:
        # Check if row truly has no gold match
        # Simplified: assume all rows have gold match
        return 0.0, "Anomaly flagged"
    
    return 0.0, "Unknown action type"
