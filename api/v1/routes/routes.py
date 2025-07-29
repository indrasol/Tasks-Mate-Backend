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