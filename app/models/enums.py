from enum import Enum


class RoleEnum(str, Enum):
    """Role enum for organization and project members"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class ProjectStatusEnum(str, Enum):
    """Project status enum"""
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    ON_HOLD = "on_hold"
    BLOCKED = "blocked"
    PAUSED = "paused"


class TaskStatusEnum(str, Enum):
    """Task status enum"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    ON_HOLD = "on_hold"


class PriorityEnum(str, Enum):
    """Priority enum for projects and tasks"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"
    CRITICAL = "critical"


class DesignationEnum(str, Enum):
    """Designation enum for team members"""
    DEVELOPER = "developer"
    DESIGNER = "designer"
    QA = "qa"
    PRODUCT_MANAGER = "product_manager"
    DEVOPS_ENGINEER = "devops_engineer"
    DEVOPS = "devops"
    ANALYST = "analyst"
    TEAM_LEAD = "team_lead"
    TESTER = "tester"
    DIRECTOR = "director"
    MANAGER = "manager"
    UI_ENGINEER = "ui_engineer"


class InviteStatusEnum(str, Enum):
    """Invite status enum"""
    PENDING = "pending"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    ACCEPTED = "accepted" 