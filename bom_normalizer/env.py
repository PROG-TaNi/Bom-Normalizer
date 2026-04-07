"""
BOM Environment Core
Main environment class implementing OpenEnv interface
"""

from typing import Tuple, Dict, Optional
from .models import (
    BOMRow, Action, ActionType, Observation, Reward, 
    RowStatus, StepResponse
)
from .generator import generate_bom
from .reward import compute_reward
from .grader import grade


class BOMEnv:
    """BOM Normalization Environment"""
    
    def __init__(self, task_id: str = 'easy', seed: int = 42):
        """
        Initialize environment
        
        Args:
            task_id: Task identifier ('easy', 'medium', 'hard')
            seed: Random seed for deterministic generation
        """
        self.task_id = task_id
        self.seed = seed
        
        self._rows = []
        self._gold = []
        self._step_count = 0
        self._cumulative_reward = 0.0
        self._done = False
        self._last_action = None
        self._last_reward = 0.0
        self.action_history = []
        self.last_action_result = None
        self.hint_budget = 3
        self.normalized_fields_count = 0
        
        # Task configurations
        self._task_configs = {
            'easy': {
                'description': 'Normalize vendor names across 10 BOM rows',
                'max_steps': 30
            },
            'medium': {
                'description': 'Normalize vendor, value, and package across 50 rows',
                'max_steps': 100
            },
            'hard': {
                'description': 'Full normalization + deduplication across 100 rows including edge cases and duplicates',
                'max_steps': 250
            }
        }
        
        self._max_steps = self._task_configs[task_id]['max_steps']
    
    def reset(self) -> Observation:
        """
        Reset environment to initial state
        
        Returns:
            Initial observation
        """
        # Generate new BOM
        self._rows, self._gold = generate_bom(self.seed, self.task_id)
        
        # Reset episode state
        self._step_count = 0
        self._cumulative_reward = 0.0
        self._done = False
        self._last_action = None
        self._last_reward = 0.0
        self.action_history = []
        self.last_action_result = None
        self.hint_budget = 3
        self.normalized_fields_count = 0
        
        return self._get_observation()
    
    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict]:
        """
        Execute one step in the environment
        
        Args:
            action: Action to execute
        
        Returns:
            (observation, reward, done, info) tuple
        """
        if self._done:
            raise RuntimeError("Episode is done. Call reset() to start new episode.")
        
        # Compute reward
        reward_value, reward_reason = compute_reward(action, self._rows, self._gold)
        
        # Apply action
        self._apply_action(action)
        
        # Update state
        self._step_count += 1
        self._cumulative_reward += reward_value
        self._last_action = action
        self._last_reward = reward_value
        
        # Check if done
        if action.action_type == ActionType.SUBMIT or self._step_count >= self._max_steps:
            self._done = True
        
        # Create reward object
        reward_obj = Reward(
            value=reward_value,
            reason=reward_reason,
            cumulative=self._cumulative_reward
        )
        
        # Create info dict
        info = {}
        if self._done:
            info['score'] = grade(self._rows, self._gold, self.task_id)
        
        # Get observation
        obs = self._get_observation()
        
        return obs, reward_obj, self._done, info
    
    def state(self) -> Observation:
        """
        Get current state without advancing episode
        
        Returns:
            Current observation
        """
        return self._get_observation()
    
    def _apply_action(self, action: Action):
        """Apply action to environment state"""
        if action.action_type == ActionType.SUBMIT:
            return
        
        # Handle INSPECT_ROW action
        if action.action_type == ActionType.INSPECT_ROW:
            if self.hint_budget > 0 and action.row_id:
                row_idx = action.row_id - 1
                if 0 <= row_idx < len(self._rows):
                    gold_row = self._gold[row_idx]
                    hint_parts = []
                    
                    # Provide hints about what's wrong
                    if self._rows[row_idx].vendor_name != gold_row.vendor_name:
                        hint_parts.append(f"vendor should be '{gold_row.vendor_name}'")
                    if self._rows[row_idx].value != gold_row.value:
                        hint_parts.append(f"value should be '{gold_row.value}'")
                    if self._rows[row_idx].package != gold_row.package:
                        hint_parts.append(f"package should be '{gold_row.package}'")
                    
                    if hint_parts:
                        self.last_action_result = f"Hint for row {action.row_id}: " + ", ".join(hint_parts)
                    else:
                        self.last_action_result = f"Row {action.row_id} is already correct"
                    
                    self.hint_budget -= 1
                else:
                    self.last_action_result = f"Invalid row_id: {action.row_id}"
            else:
                self.last_action_result = "No hints remaining" if self.hint_budget == 0 else "Invalid row_id"
            return
        
        # Handle UNDO_LAST action
        if action.action_type == ActionType.UNDO_LAST:
            if self.action_history:
                # Restore previous state
                prev_state = self.action_history.pop()
                self._rows = prev_state['rows']
                self.normalized_fields_count = prev_state['normalized_fields_count']
                self.last_action_result = "Undid last action"
            else:
                self.last_action_result = "No actions to undo"
            return
        
        # Handle BATCH_NORMALIZE action
        if action.action_type == ActionType.BATCH_NORMALIZE:
            if action.field and action.from_value and action.new_value:
                # Save state before batch operation
                self._save_state()
                
                count = 0
                for row in self._rows:
                    if action.field == "vendor_name" and row.vendor_name == action.from_value:
                        row.vendor_name = action.new_value
                        row.status = RowStatus.NORMALIZED
                        count += 1
                    elif action.field == "value" and row.value == action.from_value:
                        row.value = action.new_value
                        row.status = RowStatus.NORMALIZED
                        count += 1
                    elif action.field == "package" and row.package == action.from_value:
                        row.package = action.new_value
                        row.status = RowStatus.NORMALIZED
                        count += 1
                
                self.last_action_result = f"Batch normalized {count} rows"
            else:
                self.last_action_result = "Invalid batch_normalize parameters"
            return
        
        if action.row_id is None or action.row_id < 1 or action.row_id > len(self._rows):
            self.last_action_result = f"Invalid row_id: {action.row_id}"
            return
        
        # Save state before modifying (for undo)
        self._save_state()
        
        row_idx = action.row_id - 1
        row = self._rows[row_idx]
        
        # Apply normalization actions
        if action.action_type == ActionType.NORMALIZE_VENDOR and action.new_value:
            row.vendor_name = action.new_value
            row.status = RowStatus.NORMALIZED
            self.last_action_result = f"Normalized vendor for row {action.row_id}"
        
        elif action.action_type == ActionType.NORMALIZE_VALUE and action.new_value:
            row.value = action.new_value
            row.status = RowStatus.NORMALIZED
            self.last_action_result = f"Normalized value for row {action.row_id}"
        
        elif action.action_type == ActionType.NORMALIZE_PACKAGE and action.new_value:
            row.package = action.new_value
            row.status = RowStatus.NORMALIZED
            self.last_action_result = f"Normalized package for row {action.row_id}"
        
        elif action.action_type == ActionType.NORMALIZE_PART and action.new_value:
            row.part_number = action.new_value
            row.status = RowStatus.NORMALIZED
            self.last_action_result = f"Normalized part number for row {action.row_id}"
        
        elif action.action_type == ActionType.MERGE_ROWS and action.duplicate_row_id:
            row.merged_into = action.duplicate_row_id
            row.status = RowStatus.MERGED
            self.last_action_result = f"Merged row {action.row_id} into row {action.duplicate_row_id}"
        
        elif action.action_type == ActionType.FLAG_ANOMALY:
            row.status = RowStatus.FLAGGED
            self.last_action_result = f"Flagged row {action.row_id} as anomaly"
    
    def _save_state(self):
        """Save current state for undo functionality"""
        # Deep copy rows
        import copy
        self.action_history.append({
            'rows': copy.deepcopy(self._rows),
            'normalized_fields_count': self.normalized_fields_count
        })
    
    def _get_observation(self) -> Observation:
        """Build current observation"""
        # Count fields remaining
        fields_remaining = self._count_fields_remaining()
        
        return Observation(
            task_id=self.task_id,
            task_description=self._task_configs[self.task_id]['description'],
            rows=self._rows,
            step_count=self._step_count,
            max_steps=self._max_steps,
            fields_remaining=fields_remaining,
            last_action=self._last_action,
            last_reward=self._last_reward,
            cumulative_reward=self._cumulative_reward,
            done=self._done,
            info={},
            hint_budget=self.hint_budget,
            last_action_result=self.last_action_result
        )
    
    def _count_fields_remaining(self) -> int:
        """Count fields still needing correction"""
        remaining = 0
        
        for row, gold_row in zip(self._rows, self._gold):
            if gold_row.merged_into:
                if row.status != RowStatus.MERGED:
                    remaining += 1
                continue
            if row.vendor_name != gold_row.vendor_name:
                remaining += 1
            if row.value != gold_row.value:
                remaining += 1
            if row.package != gold_row.package:
                remaining += 1
            if row.part_number != gold_row.part_number:
                remaining += 1
        
        return remaining
