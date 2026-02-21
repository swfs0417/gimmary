from fastapi import APIRouter, Depends
from gimmary.app.auth.utils import get_current_user
from gimmary.app.missions.schemes import MissionCreateRequest, MissionUpdateRequest, MissionResponse

router = APIRouter(prefix="/missions", tags=["missions"])

@router.post("/")
def create_mission(request: MissionCreateRequest, current_user=Depends(get_current_user)) -> MissionResponse:
  pass

@router.get("/{mission_id}")
def get_mission(mission_id: int, current_user=Depends(get_current_user)) -> MissionResponse:
  pass

@router.patch("/{mission_id}")
def update_mission(mission_id: int, request: MissionUpdateRequest, current_user=Depends(get_current_user)) -> MissionResponse:
  pass

@router.delete("/{mission_id}", status_code=204)
def delete_mission(mission_id: int, current_user=Depends(get_current_user)):
  pass