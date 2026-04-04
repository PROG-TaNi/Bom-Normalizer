"""
Tests for BOM Environment
"""

import pytest
from bom_normalizer.env import BOMEnv
from bom_normalizer.models import Action, ActionType


def test_env_initialization():
    """Test environment initialization"""
    env = BOMEnv(task_id='easy', seed=42)
    assert env.task_id == 'easy'
    assert env.seed == 42


def test_env_reset():
    """Test environment reset"""
    env = BOMEnv(task_id='easy', seed=42)
    obs = env.reset()
    
    assert obs.task_id == 'easy'
    assert obs.step_count == 0
    assert obs.cumulative_reward == 0.0
    assert obs.done == False
    assert len(obs.rows) == 10  # Easy task has 10 rows


def test_env_step():
    """Test environment step"""
    env = BOMEnv(task_id='easy', seed=42)
    env.reset()
    
    action = Action(
        action_type=ActionType.NORMALIZE_VENDOR,
        row_id=1,
        new_value='Texas Instruments'
    )
    
    obs, reward, done, info = env.step(action)
    
    assert obs.step_count == 1
    assert isinstance(reward.value, float)
    assert isinstance(done, bool)


def test_env_submit():
    """Test submit action"""
    env = BOMEnv(task_id='easy', seed=42)
    env.reset()
    
    action = Action(action_type=ActionType.SUBMIT)
    obs, reward, done, info = env.step(action)
    
    assert done == True
    assert 'score' in info


def test_env_max_steps():
    """Test max steps limit"""
    env = BOMEnv(task_id='easy', seed=42)
    env.reset()
    
    # Take max_steps actions
    for _ in range(30):
        action = Action(
            action_type=ActionType.NORMALIZE_VENDOR,
            row_id=1,
            new_value='Test'
        )
        obs, reward, done, info = env.step(action)
        
        if done:
            break
    
    assert done == True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
