from enum import Enum

class PipelineStepType(str, Enum):
    VALIDATE = "validate"
    TRANSFORM = "transform"
    ENRICH = "enrich"
    LOAD = "load"
    BUSINESS_RULES = "business_rules"

class PipelineRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped" 