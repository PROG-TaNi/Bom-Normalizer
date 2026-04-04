"""
Data models for BOM Normalizer Environment
All Pydantic v2 models with strict validation
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class RowStatus(str, Enum):
    """Status of a BOM row"""
    RAW = "raw"                 # Untouched since reset()
    NORMALIZED = "normalized"   # Agent has acted on this row
    FLAGGED = "flagged"         # Agent flagged as anomaly/bad data
    MERGED = "merged"           # Row merged into another (Hard task only)


class BOMRow(BaseModel):
    """Single row in a Bill of Materials"""
    row_id: int = Field(..., description="Stable ID, 1-indexed")
    vendor_name: str = Field(..., description="Vendor/manufacturer name")
    part_number: str = Field(..., description="Part number/SKU")
    value: str = Field(..., description="Component value (resistance, capacitance, etc)")
    package: str = Field(..., description="Package code (e.g., SOT-23, 0402)")
    quantity: int = Field(..., description="Quantity needed")
    status: RowStatus = Field(default=RowStatus.RAW, description="Current row status")
    merged_into: Optional[int] = Field(default=None, description="Row ID of canonical row if merged")

    model_config = ConfigDict(extra='forbid')


class ActionType(str, Enum):
    """Available action types"""
    NORMALIZE_VENDOR = "normalize_vendor"
    NORMALIZE_VALUE = "normalize_value"
    NORMALIZE_PACKAGE = "normalize_package"
    NORMALIZE_PART = "normalize_part"
    MERGE_ROWS = "merge_rows"
    FLAG_ANOMALY = "flag_anomaly"
    INSPECT_ROW = "inspect_row"
    BATCH_NORMALIZE = "batch_normalize"
    UNDO_LAST = "undo_last"
    SUBMIT = "submit"


class Action(BaseModel):
    """Action to be taken by the agent"""
    action_type: ActionType = Field(..., description="Type of action to perform")
    row_id: Optional[int] = Field(default=None, description="Target row ID")
    new_value: Optional[str] = Field(default=None, description="New normalized value")
    duplicate_row_id: Optional[int] = Field(default=None, description="For MERGE_ROWS: canonical row ID")
    field: Optional[str] = Field(default=None, description="For BATCH_NORMALIZE: field to normalize (vendor_name/value/package)")
    from_value: Optional[str] = Field(default=None, description="For BATCH_NORMALIZE: value to replace")

    model_config = ConfigDict(extra='forbid')


class Observation(BaseModel):
    """Environment observation returned to agent"""
    task_id: str = Field(..., description="Task identifier (easy/medium/hard)")
    task_description: str = Field(..., description="Human-readable task objective")
    rows: List[BOMRow] = Field(..., description="Current state of all BOM rows")
    step_count: int = Field(..., description="Current step number")
    max_steps: int = Field(..., description="Maximum steps allowed")
    fields_remaining: int = Field(..., description="Fields still needing correction")
    last_action: Optional[Action] = Field(default=None, description="Last action taken")
    last_reward: float = Field(default=0.0, description="Reward from last action")
    cumulative_reward: float = Field(default=0.0, description="Total reward this episode")
    done: bool = Field(default=False, description="Episode completed")
    info: dict = Field(default_factory=dict, description="Extra diagnostic data")
    hint_budget: int = Field(default=3, description="Remaining INSPECT_ROW hints available")
    last_action_result: Optional[str] = Field(default=None, description="Result message from last action")

    model_config = ConfigDict(extra='forbid')


class Reward(BaseModel):
    """Reward information"""
    value: float = Field(..., description="Immediate reward this step")
    reason: str = Field(..., description="Human-readable explanation")
    cumulative: float = Field(..., description="Total reward so far this episode")

    model_config = ConfigDict(extra='forbid')


class StepResponse(BaseModel):
    """Response from step() endpoint"""
    observation: Observation
    reward: Reward
    done: bool
    info: dict

    model_config = ConfigDict(extra='forbid')
