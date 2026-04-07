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
    """Check if row_id should be merged into dup_id according to gold standard"""
    if row_id < 1 or row_id > len(gold):
        return False
    gold_row = gold[row_id - 1]
    return gold_row.merged_into == dup_id


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
    
    # INSPECT_ROW — costs a hint but provides information
    if action.action_type == ActionType.INSPECT_ROW:
        return -0.02, "Hint used (inspect_row)"
    
    # UNDO_LAST — small cost for reverting
    if action.action_type == ActionType.UNDO_LAST:
        return -0.01, "Undo action"
    
    # BATCH_NORMALIZE — reward based on correctness across all affected rows
    if action.action_type == ActionType.BATCH_NORMALIZE:
        if not action.field or not action.from_value or not action.new_value:
            return -0.05, "Invalid batch_normalize parameters"
        
        field_name = action.field
        if field_name not in ('vendor_name', 'value', 'package'):
            return -0.05, f"Invalid field for batch_normalize: {field_name}"
        
        correct = 0
        incorrect = 0
        total = 0
        
        for row, gold_row in zip(rows, gold):
            if gold_row.merged_into:
                continue
            current_val = getattr(row, field_name)
            if current_val == action.from_value:
                total += 1
                gold_val = getattr(gold_row, field_name)
                if action.new_value == gold_val:
                    correct += 1
                elif action.new_value.lower() == gold_val.lower():
                    correct += 0.8
                else:
                    incorrect += 1
        
        if total == 0:
            return 0.0, "No rows matched from_value"
        
        reward = correct * 0.15 - incorrect * 0.10
        return round(reward, 4), f"Batch: {int(correct)}/{total} correct normalizations"
    
    # FLAG_ANOMALY — no row_id required
    if action.action_type == ActionType.FLAG_ANOMALY:
        if action.row_id and 1 <= action.row_id <= len(gold):
            gold_row = gold[action.row_id - 1]
            if gold_row.merged_into:
                return 0.05, "Correctly flagged duplicate row"
        return 0.0, "Anomaly flagged"
    
    # All remaining actions require a valid row_id
    if action.row_id is None or action.row_id < 1 or action.row_id > len(rows):
        return -0.05, "Invalid row_id"
    
    row_idx = action.row_id - 1
    current_row = rows[row_idx]
    
    if row_idx >= len(gold):
        return -0.05, "Row not in gold standard"
    
    gold_row = gold[row_idx]
    
    # MERGE_ROWS action
    if action.action_type == ActionType.MERGE_ROWS:
        if action.duplicate_row_id is None:
            return -0.05, "Missing duplicate_row_id for merge action"
        
        if _is_true_duplicate(action.row_id, action.duplicate_row_id, gold):
            return 0.20, "Correct duplicate pair detected"
        else:
            return -0.05, "Incorrect duplicate pair"
    
    # NORMALIZE actions
    if action.action_type in [
        ActionType.NORMALIZE_VENDOR,
        ActionType.NORMALIZE_VALUE,
        ActionType.NORMALIZE_PACKAGE,
        ActionType.NORMALIZE_PART
    ]:
        if action.new_value is None:
            return -0.05, "Missing new_value for normalize action"
        
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
        
        if current_val == gold_val and new_val != gold_val:
            return -0.15, f"Corrupted correct {current_field}"
        
        if current_val == gold_val and new_val == gold_val:
            return 0.02, f"Field already correct (no change needed)"
        
        if new_val == gold_val:
            return 0.30, f"Perfect {current_field} normalization"
        
        if new_val.lower() == gold_val.lower():
            return 0.25, f"Correct {current_field} (case mismatch)"
        
        if new_val.lower() in gold_val.lower() or gold_val.lower() in new_val.lower():
            return 0.15, f"Partial {current_field} match (substring)"
        
        similarity = _calculate_string_similarity(new_val.lower(), gold_val.lower())
        if similarity > 0.7:
            return 0.10, f"Similar {current_field} (similarity: {similarity:.2f})"
        
        if similarity > 0.5:
            return 0.05, f"Somewhat similar {current_field} (similarity: {similarity:.2f})"
        
        if action.action_type == ActionType.NORMALIZE_VALUE:
            if _numeric_close(new_val, gold_val):
                return 0.20, f"Numerically equivalent {current_field}"
        
        if similarity > 0.3:
            return 0.0, f"Incorrect {current_field} (low similarity: {similarity:.2f})"
        
        return -0.05, f"Very incorrect {current_field} normalization"
    
    return 0.0, "Unknown action type"
