from fastapi import APIRouter
from gimmary.app.users.router import user_router
from gimmary.app.team.router import team_router
from gimmary.app.missions.router import router as missions_router
from gimmary.app.groups.router import groups_router

api_router = APIRouter()

api_router.include_router(user_router)
api_router.include_router(team_router)
api_router.include_router(missions_router)
api_router.include_router(groups_router)
# router.include_router()