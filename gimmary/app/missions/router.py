from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from sqlalchemy.orm import Session
from datetime import datetime

from gimmary.app.auth.utils import get_current_user
from gimmary.app.missions.schemes import (
  MissionCreateRequest, MissionUpdateRequest, MissionResponse,
  GroupMissionUpdateRequest, GroupMissionResponse,
)
from gimmary.database.connection import get_db_session
from gimmary.database.models import Mission, GroupMission, TeamMember, User, UserRole

router = APIRouter(prefix="/missions", tags=["missions"])


@router.post("/", response_model=MissionResponse)
def create_mission(
  request: MissionCreateRequest,
  current_user: User = Depends(get_current_user),
  db: Annotated[Session, Depends(get_db_session)] = None,
):
  # 해당 팀의 어드민인지 확인
  membership = db.query(TeamMember).filter(
    TeamMember.team_id == request.team_id,
    TeamMember.user_id == current_user.id,
    TeamMember.role == UserRole.ADMIN.value
  ).first()
  if not membership:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only team admin can create missions")

  mission = Mission(
    team_id=request.team_id,
    title=request.title,
    description=request.description,
    created_at=datetime.utcnow(),
  )
  db.add(mission)
  db.commit()
  db.refresh(mission)
  return MissionResponse(
    id=mission.id,
    team_id=mission.team_id,
    title=mission.title,
    description=mission.description,
    created_at=mission.created_at.isoformat(),
  )


@router.get("/{mission_id}", response_model=MissionResponse)
def get_mission(
  mission_id: int,
  db: Annotated[Session, Depends(get_db_session)] = None,
):
  mission = db.query(Mission).filter(Mission.id == mission_id).first()
  if not mission:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
  return MissionResponse(
    id=mission.id,
    team_id=mission.team_id,
    title=mission.title,
    description=mission.description,
    created_at=mission.created_at.isoformat() if mission.created_at else "",
  )


@router.patch("/{mission_id}", response_model=MissionResponse)
def update_mission(
  mission_id: int,
  request: MissionUpdateRequest,
  current_user: User = Depends(get_current_user),
  db: Annotated[Session, Depends(get_db_session)] = None,
):
  mission = db.query(Mission).filter(Mission.id == mission_id).first()
  if not mission:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")

  membership = db.query(TeamMember).filter(
    TeamMember.team_id == mission.team_id,
    TeamMember.user_id == current_user.id,
    TeamMember.role == UserRole.ADMIN.value
  ).first()
  if not membership:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only team admin can update missions")

  if request.title is not None:
    mission.title = request.title
  if request.description is not None:
    mission.description = request.description

  db.commit()
  db.refresh(mission)
  return MissionResponse(
    id=mission.id,
    team_id=mission.team_id,
    title=mission.title,
    description=mission.description,
    created_at=mission.created_at.isoformat() if mission.created_at else "",
  )


@router.delete("/{mission_id}", status_code=204)
def delete_mission(
  mission_id: int,
  current_user: User = Depends(get_current_user),
  db: Annotated[Session, Depends(get_db_session)] = None,
):
  mission = db.query(Mission).filter(Mission.id == mission_id).first()
  if not mission:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")

  membership = db.query(TeamMember).filter(
    TeamMember.team_id == mission.team_id,
    TeamMember.user_id == current_user.id,
    TeamMember.role == UserRole.ADMIN.value
  ).first()
  if not membership:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only team admin can delete missions")

  db.delete(mission)
  db.commit()


@router.get("/{mission_id}/groups/{group_id}", response_model=GroupMissionResponse)
def get_group_mission(
  mission_id: int,
  group_id: int,
  db: Annotated[Session, Depends(get_db_session)] = None,
):
  gm = db.query(GroupMission).filter(
    GroupMission.mission_id == mission_id,
    GroupMission.group_id == group_id
  ).first()
  if not gm:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="GroupMission not found")
  return GroupMissionResponse(
    id=gm.id,
    mission_id=gm.mission_id,
    group_id=gm.group_id,
    status=gm.status,
  )

@router.patch("/{mission_id}/groups/{group_id}", response_model=GroupMissionResponse)
def update_group_mission(
  mission_id: int,
  group_id: int,
  request: GroupMissionUpdateRequest,
  current_user: User = Depends(get_current_user),
  db: Annotated[Session, Depends(get_db_session)] = None,
):
  gm = db.query(GroupMission).filter(
    GroupMission.mission_id == mission_id,
    GroupMission.group_id == group_id
  ).first()
  if not gm:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="GroupMission not found")

  if request.status is not None:
    gm.status = request.status

  db.commit()
  db.refresh(gm)
  return GroupMissionResponse(
    id=gm.id,
    mission_id=gm.mission_id,
    group_id=gm.group_id,
    status=gm.status,
  )