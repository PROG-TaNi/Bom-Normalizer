"""
Task Definitions
Configuration for each difficulty level
"""

from typing import Dict, Any


TASK_CONFIGS: Dict[str, Dict[str, Any]] = {
    'easy': {
        'id': 'easy',
        'description': 'Normalize vendor names across 10 BOM rows',
        'difficulty': 'easy',
        'max_steps': 30,
        'row_count': 10,
        'fields_to_normalize': ['vendor_name'],
        'baseline_score': 0.85,
        'grading_weights': {
            'vendor_name': 1.0
        }
    },
    'medium': {
        'id': 'medium',
        'description': 'Normalize vendor, value, and package across 50 rows',
        'difficulty': 'medium',
        'max_steps': 100,
        'row_count': 50,
        'fields_to_normalize': ['vendor_name', 'value', 'package'],
        'baseline_score': 0.55,
        'grading_weights': {
            'vendor_name': 0.33,
            'value': 0.33,
            'package': 0.34
        }
    },
    'hard': {
        'id': 'hard',
        'description': 'Full normalization + deduplication across 100 rows including edge cases and duplicates',
        'difficulty': 'hard',
        'max_steps': 250,
        'row_count': 50,  # Base 50, grows to ~100 with duplicates and edge cases
        'fields_to_normalize': ['vendor_name', 'value', 'package', 'part_number'],
        'baseline_score': 0.25,
        'grading_weights': {
            'field_normalization': 0.5,
            'duplicate_detection': 0.3,
            'quantity_aggregation': 0.2
        },
        'duplicate_pairs': 40
    }
}


def get_task_config(task_id: str) -> Dict[str, Any]:
    """
    Get configuration for a task
    
    Args:
        task_id: Task identifier ('easy', 'medium', 'hard')
    
    Returns:
        Task configuration dictionary
    
    Raises:
        ValueError: If task_id is unknown
    """
    if task_id not in TASK_CONFIGS:
        raise ValueError(f"Unknown task_id: {task_id}")
    
    return TASK_CONFIGS[task_id]


def list_tasks() -> list:
    """Get list of all task IDs"""
    return list(TASK_CONFIGS.keys())
