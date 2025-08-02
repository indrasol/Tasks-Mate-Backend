from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, ARRAY, JSON, Float, Date, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy import Date
from uuid import uuid4
from enum import Enum
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from models.enums import RoleEnum, ProjectStatusEnum, TaskStatusEnum, PriorityEnum, DesignationEnum, InviteStatusEnum

from sqlalchemy import Column, String, Text, Boolean, DateTime, Date, ForeignKey, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

# Base class for declarative models
Base = declarative_base()

# Junction table for many-to-many relationship between User and Tenant
class UserTenantAssociation(Base):
    __tablename__ = "user_tenant_association"
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    projects = relationship("Project", back_populates="user")
    roles = relationship("Role", back_populates="user")
    tenants = relationship("Tenant", secondary="user_tenant_association", back_populates="users")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Organization(Base):
    __tablename__ = "organizations"
    org_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    description = Column(Text)
    logo = Column(Text)
    email = Column(Text)
    metadata = Column(JSON, default=dict)
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    deleted_at = Column(DateTime)
    delete_reason = Column(Text)

class Role(Base):
    __tablename__ = "roles"
    role_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    permissions = Column(JSON, default=dict)
    updated_at = Column(DateTime)

class Designation(Base):
    __tablename__ = "designations"
    designation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    metadata = Column(JSON, default=dict)
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class OrganizationInvite(Base):
    __tablename__ = "organization_invites"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.org_id"), nullable=False)
    email = Column(Text, nullable=False)
    designation = Column(UUID(as_uuid=True), ForeignKey("designations.designation_id"))
    role = Column(UUID(as_uuid=True), ForeignKey("roles.role_id"))
    invited_by = Column(UUID(as_uuid=True))
    invite_status = Column(SQLAlchemyEnum(InviteStatusEnum), default=InviteStatusEnum.PENDING)
    sent_at = Column(DateTime)
    expires_at = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    is_cancelled = Column(Boolean, default=False)
    cancel_date = Column(DateTime)

class OrganizationMember(Base):
    __tablename__ = "organization_members"
    user_id = Column(UUID(as_uuid=True), primary_key=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.org_id"), primary_key=True)
    designation = Column(UUID(as_uuid=True), ForeignKey("designations.designation_id"))
    role = Column(UUID(as_uuid=True), ForeignKey("roles.role_id"))
    permissions = Column(JSON, default=dict)
    invited_by = Column(UUID(as_uuid=True))
    is_active = Column(Boolean, default=True)
    invited_at = Column(DateTime)
    accepted_at = Column(DateTime)
    updated_at = Column(DateTime)
    deleted_at = Column(DateTime)
    delete_reason = Column(Text)
    deleted_by = Column(UUID(as_uuid=True))
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))

class Project(Base):
    __tablename__ = "projects"
    project_id = Column(Text, primary_key=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.org_id"), nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text)
    metadata = Column(JSON, default=dict)
    status = Column(SQLAlchemyEnum(ProjectStatusEnum), default=ProjectStatusEnum.NOT_STARTED)
    priority = Column(SQLAlchemyEnum(PriorityEnum), default=PriorityEnum.NONE)
    start_date = Column(Date)
    end_date = Column(Date)
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    deleted_at = Column(DateTime)
    delete_reason = Column(Text)

class ProjectMember(Base):
    __tablename__ = "project_members"
    project_id = Column(Text, ForeignKey("projects.project_id"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), primary_key=True)
    designation = Column(UUID(as_uuid=True), ForeignKey("designations.designation_id"))
    role = Column(UUID(as_uuid=True), ForeignKey("roles.role_id"))
    permissions = Column(JSON, default=dict)
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    deleted_at = Column(DateTime)
    delete_reason = Column(Text)
    # deleted_by = Column(UUID(as_uuid=True))

class ProjectResource(Base):
    __tablename__ = "project_resources"
    resource_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Text, ForeignKey("projects.project_id"), nullable=False)
    name = Column(Text, nullable=False)
    url = Column(Text)
    resource_type = Column(Text)
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    deleted_at = Column(DateTime)
    delete_reason = Column(Text)

class Task(Base):
    __tablename__ = "tasks"
    task_id = Column(Text, primary_key=True)
    project_id = Column(Text, ForeignKey("projects.project_id"), nullable=False)
    sub_tasks = Column(ARRAY(Text), default=list)
    dependencies = Column(ARRAY(Text), default=list)
    title = Column(Text, nullable=False)
    description = Column(Text)
    status = Column(SQLAlchemyEnum(TaskStatusEnum), default=TaskStatusEnum.NOT_STARTED)
    assignee_id = Column(UUID(as_uuid=True))
    due_date = Column(Date)
    priority = Column(SQLAlchemyEnum(PriorityEnum), default=PriorityEnum.NONE)
    tags = Column(ARRAY(Text), default=list)
    metadata = Column(ARRAY(JSON), default=list)
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class TaskAttachment(Base):
    __tablename__ = "task_attachments"
    attachment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(Text, nullable=False)
    title = Column(Text)
    name = Column(Text)
    url = Column(Text)
    uploaded_by = Column(UUID(as_uuid=True))
    uploaded_at = Column(DateTime)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID(as_uuid=True))
    is_inline = Column(Boolean, default=False)

class TaskComment(Base):
    __tablename__ = "task_comments"
    comment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(Text, nullable=False)
    title = Column(Text)
    user_id = Column(UUID(as_uuid=True))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class TaskHistory(Base):
    __tablename__ = "tasks_history"
    history_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(Text, nullable=False)
    title = Column(Text)
    metadata = Column(ARRAY(JSON), default=list)
    hash_id = Column(Text)
    updated_at = Column(DateTime)

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)  
    users = relationship("User", secondary="user_tenant_association", back_populates="tenants")
    projects = relationship("Project", back_populates="tenant")
    templates = relationship("Template", back_populates="tenant")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    roles = relationship("Role", back_populates="tenant")

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    project_code = Column(String, ForeignKey("projects.project_code"), nullable=False)
    role_name = Column(String)  # e.g., "admin", "editor"
    permissions = Column(JSONB, default={"view": True, "edit": False})  # JSONB for permissions
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    user = relationship("User", back_populates="roles")
    tenant = relationship("Tenant", back_populates="roles")
    project = relationship("Project", back_populates="roles")

class Session(Base):
    """SQLAlchemy model for sessions table.
    
    Maps to the sessions table in the database. This table tracks active sessions
    for users and projects, allowing session resumption beyond Redis TTL expiry.
    """
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False, unique=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    project_id = Column(String, nullable=False, index=True)
    version = Column(Integer, default=0, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_accessed = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, nullable=False, default=True)
    
    def __repr__(self):
        return f"<Session(session_id='{self.session_id}', user_id='{self.user_id}', project_id='{self.project_id}')>"

class Sessions(BaseModel):
    """
    Sessions table model - Tracks active sessions for users and projects.
    This provides persistence for session IDs beyond Redis TTL expiry.
    
    The actual session content is stored in Redis, while this table
    stores metadata about sessions to allow users to resume their work.
    """
    id: Optional[int] = Field(None, description="Auto-increment primary key")
    session_id: str = Field(..., description="Unique session identifier (UUID)")
    user_id: str = Field(..., description="User ID associated with the session")
    project_id: str = Field(..., description="Project ID associated with the session")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Session creation timestamp")
    last_accessed: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last time the session was accessed")
    is_active: bool = Field(default=True, description="Whether the session is still active")
    
    model_config = ConfigDict(
        from_attributes=True,         # was orm_mode
        json_schema_extra={           # was schema_extra
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user123",
                "project_id": "project456",
                "created_at": "2023-09-01T12:00:00Z",
                "last_accessed": "2023-09-01T14:30:00Z",
                "is_active": True
            }
        }
    )

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    details = Column(JSON, default=dict)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    type = Column(String, nullable=False)
    message = Column(String, nullable=False)
    resource_id = Column(String)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

