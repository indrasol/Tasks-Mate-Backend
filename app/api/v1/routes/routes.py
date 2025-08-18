# routes.py (Main router file)
from fastapi import APIRouter

# Register Routes
from app.api.v1.routes.register.register import router as register_router
from app.api.v1.routes.register.login import router as login_router
from app.api.v1.routes.register.auth import router as auth_router
from app.api.v1.routes.organizations.organization_router import router as organization_router
from app.api.v1.routes.projects.project_router import router as project_router
from app.api.v1.routes.tasks.task_router import router as task_router
from app.api.v1.routes.organizations.member_router import router as organization_member_router
from app.api.v1.routes.organizations.invite_router import router as organization_invite_router
from app.api.v1.routes.organizations.designation_router import router as designation_router
from app.api.v1.routes.projects.member_router import router as project_member_router
from app.api.v1.routes.projects.resource_router import router as project_resource_router
from app.api.v1.routes.tasks.attachment_router import router as task_attachment_router
from app.api.v1.routes.tasks.comment_router import router as task_comment_router
from app.api.v1.routes.tasks.history_router import router as task_history_router
from app.api.v1.routes.projects.stats_router import router as project_stats_router
from app.api.v1.routes.dashboard.dashboard_router import router as dashboard_router


router = APIRouter()


# Register Routes
router.include_router(register_router, tags=["Register - sign_up_router"])
router.include_router(login_router, tags=["Register - login_router"])
router.include_router(auth_router, tags=["Register - auth_router"])
router.include_router(organization_router, prefix="/organizations", tags=["Organizations"])
router.include_router(project_router, prefix="/projects", tags=["Projects"])
router.include_router(task_router, prefix="/tasks", tags=["Tasks"])
router.include_router(organization_member_router, prefix="/organization-members", tags=["Organization Members"])
router.include_router(organization_invite_router, prefix="/organization-invites", tags=["Organization Invites"])
router.include_router(designation_router, prefix="/designations", tags=["Designations"])
router.include_router(project_member_router, prefix="/project-members", tags=["Project Members"])
router.include_router(project_resource_router, prefix="/project-resources", tags=["Project Resources"])
router.include_router(task_attachment_router, prefix="/task-attachments", tags=["Task Attachments"])
router.include_router(task_comment_router, prefix="/task-comments", tags=["Task Comments"])
router.include_router(task_history_router, prefix="/task-history", tags=["Task History"])
router.include_router(project_stats_router, prefix="/project-stats", tags=["Project Stats"])
router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])