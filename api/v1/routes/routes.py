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