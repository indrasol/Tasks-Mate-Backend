# routes.py (Main router file)
from fastapi import APIRouter

# Register Routes
from api.v1.routes.register.register import router as register_router
from api.v1.routes.register.login import router as login_router
from api.v1.routes.register.auth import router as auth_router


from api.v1.routes.organizations.routes import router as organizations_router

router = APIRouter()


# Register Routes
router.include_router(register_router, tags=["Register - sign_up_router"])
router.include_router(login_router, tags=["Register - login_router"])
router.include_router(auth_router, tags=["Register - auth_router"])

router.include_router(organizations_router, tags=["Organizations - organizations_router"])
from api.v1.routes.projects.routes import router as projects_router
router.include_router(projects_router, tags=["Projects - projects_router"])
from api.v1.routes.tasks.routes import router as tasks_router
router.include_router(tasks_router, tags=["Tasks - tasks_router"])
from api.v1.routes.members.routes import router as members_router
router.include_router(members_router, tags=["Members - members_router"])
from api.v1.routes.project_teams.routes import router as project_teams_router
router.include_router(project_teams_router, tags=["Project Teams - project_teams_router"])
from api.v1.routes.task_tags.routes import router as task_tags_router
router.include_router(task_tags_router, tags=["Task Tags - task_tags_router"])