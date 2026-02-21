from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from sqlalchemy.orm import Session
from datetime import datetime

from gimmary.app.auth.utils import get_current_user
from gimmary.app.missions.schemes import MissionCreateRequest, MissionUpdateRequest, MissionResponse
from gimmary.database.connection import get_db_session
from gimmary.database.models import Mission, User

router = APIRouter(prefix="/missions", tags=["missions"])


@router.post("/")
def create_mission(
  request: MissionCreateRequest,
  current_user: User=Depends(get_current_user),
  db: Annotated[Session, Depends(get_db_session)] = None,
) -> MissionResponse:
  if not (current_user.is_admin or any(group.id == request.group_id for group in current_user.groups)):
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not belong to the specified group")
  mission = Mission(
    group_id=request.group_id,
    title=request.title,
    description=request.description,
    created_at=datetime.utcnow(),
  )
  db.add(mission)
  db.commit()
  db.refresh(mission)
  return MissionResponse(
    id=mission.id,
    group_id=mission.group_id,
    title=mission.title,
    description=mission.description,
    status=mission.status,
    decided_by_admin=bool(mission.decided_by_admin),
    created_at=mission.created_at.isoformat() if mission.created_at else "",
  )


@router.get("/{mission_id}")
def get_mission(
  mission_id: int,
  current_user: User=Depends(get_current_user),
  db: Annotated[Session, Depends(get_db_session)] = None,
) -> MissionResponse:
  mission = db.query(Mission).filter(Mission.id == mission_id).first()
  if not mission:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
  if not (current_user.is_admin or any(group.id == mission.group_id for group in current_user.groups)):
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not belong to the group of this mission")
  return MissionResponse(
    id=mission.id,
    group_id=mission.group_id,
    title=mission.title,
    description=mission.description,
    status=mission.status,
    decided_by_admin=bool(mission.decided_by_admin),
    created_at=mission.created_at.isoformat() if mission.created_at else "",
  )


@router.patch("/{mission_id}")
def update_mission(
  mission_id: int,
  request: MissionUpdateRequest,
  current_user: User=Depends(get_current_user),
  db: Annotated[Session, Depends(get_db_session)] = None,
) -> MissionResponse:
  mission = db.query(Mission).filter(Mission.id == mission_id).first()
  if not mission:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
  if not (current_user.is_admin or any(group.id == mission.group_id for group in current_user.groups)):
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not belong to the group of this mission")

  if request.title is not None:
    mission.title = request.title
  if request.description is not None:
    mission.description = request.description
  if request.status is not None:
    mission.status = request.status
  if request.decided_by_admin is not None:
    mission.decided_by_admin = request.decided_by_admin

  db.add(mission)
  db.commit()
  db.refresh(mission)

  return MissionResponse(
    id=mission.id,
    group_id=mission.group_id,
    title=mission.title,
    description=mission.description,
    status=mission.status,
    decided_by_admin=bool(mission.decided_by_admin),
    created_at=mission.created_at.isoformat() if mission.created_at else "",
  )


@router.delete("/{mission_id}", status_code=204)
def delete_mission(
  mission_id: int,
  current_user: User=Depends(get_current_user),
  db: Annotated[Session, Depends(get_db_session)] = None,
):
  mission = db.query(Mission).filter(Mission.id == mission_id).first()
  if not mission:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
  if not (current_user.is_admin or any(group.id == mission.group_id for group in current_user.groups)):
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not belong to the group of this mission")
  db.delete(mission)
  db.commit()