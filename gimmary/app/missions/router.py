from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from sqlalchemy.orm import Session
from datetime import datetime

from gimmary.app.auth.utils import get_current_user
from gimmary.app.missions.schemes import (
  MissionCreateRequest, MissionUpdateRequest, MissionResponse,
  GroupMissionUpdateRequest, GroupMissionResponse, SubmissionResponse,
)
from gimmary.database.connection import get_db_session
from gimmary.database.models import (
  Mission, GroupMission, GroupMember, TeamMember, Pictures, User, UserRole, MissionStatus
)
from gimmary.app.missions.generate_model import generate_3d_model
from fastapi import File, UploadFile
from fastapi.responses import FileResponse
from pathlib import Path
import os
import uuid

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
    points=request.points,
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
    points=mission.points,
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
    points=mission.points,
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
  if request.points is not None:
    mission.points = request.points

  db.commit()
  db.refresh(mission)
  return MissionResponse(
    id=mission.id,
    team_id=mission.team_id,
    title=mission.title,
    description=mission.description,
    points=mission.points,
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


@router.get("/{mission_id}/groups", response_model=list[GroupMissionResponse])
def get_all_group_missions(
  mission_id: int,
  db: Annotated[Session, Depends(get_db_session)] = None,
):
  mission = db.query(Mission).filter(Mission.id == mission_id).first()
  if not mission:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")

  group_missions = db.query(GroupMission).filter(GroupMission.mission_id == mission_id).all()

  return [
    GroupMissionResponse(
      id=gm.id,
      mission_id=gm.mission_id,
      group_id=gm.group_id,
      status=gm.status,
    )
    for gm in group_missions
  ]

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

@router.post("/{mission_id}/submit", response_model=SubmissionResponse)
async def submit_group_mission(
  mission_id: int,
  group_id: int,
  file: UploadFile = File(...),
  current_user: User = Depends(get_current_user),
  db: Annotated[Session, Depends(get_db_session)] = None,
):
  # 유효성 검사: mission/group 존재 확인
  gm = db.query(GroupMission).filter(
    GroupMission.mission_id == mission_id,
    GroupMission.group_id == group_id,
  ).first()
  if not gm:
    # 자동 생성 허용: group_mission이 없으면 새로 만든다
    gm = GroupMission(mission_id=mission_id, group_id=group_id)
    db.add(gm)
    db.commit()
    db.refresh(gm)

  # 제출자가 그룹의 멤버인지 확인
  membership = db.query(GroupMember).filter(
    GroupMember.group_id == group_id,
    GroupMember.user_id == current_user.id
  ).first()
  if not membership:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only group members can submit photos")

  # 파일 저장
  uploads_dir = Path("uploads") / f"group_mission_{gm.id}"
  os.makedirs(uploads_dir, exist_ok=True)
  suffix = Path(file.filename).suffix or ""
  filename = f"{current_user.id}_{uuid.uuid4().hex}{suffix}"
  dest = uploads_dir / filename
  contents = await file.read()
  dest.write_bytes(contents)

  # Pictures 레코드 생성 (누가 제출했는지 기록)
  pic = Pictures(group_mission_id=gm.id, user_id=current_user.id, url=str(dest), uploaded_at=datetime.utcnow())
  db.add(pic)
  db.commit()

  # 그룹 멤버 수와 제출한 고유 유저 수 비교
  total_members = db.query(GroupMember).filter(GroupMember.group_id == group_id).count()
  submitted_users = db.query(Pictures.user_id).filter(Pictures.group_mission_id == gm.id).distinct().count()

  # 기본 details 값
  details = {
    "uploaded": True,
    "total_members": total_members,
    "submitted_users": submitted_users,
    "model_generated": None,
    "download_url": None,
    "log": None,
    "error": None,
  }

  completed = False

  # 모두 제출했으면 모델 생성
  if submitted_users >= total_members and total_members > 0:
    completed = True
    # 이미지 경로 수집
    pics = db.query(Pictures).filter(Pictures.group_mission_id == gm.id).all()
    image_paths = [p.url for p in pics]

    try:
      gen = generate_3d_model(image_paths, use_verify=True)
      details["log"] = gen.get("log", "")
      if gen.get("success") and gen.get("mesh_path"):
        downloads_dir = Path("downloads")
        downloads_dir.mkdir(parents=True, exist_ok=True)
        dest_name = f"model_{gm.id}_{uuid.uuid4().hex}.glb"
        final_path = downloads_dir / dest_name
        Path(gen["mesh_path"]).replace(final_path)

        # 상태 업데이트
        gm.status = MissionStatus.SUCCESS.value
        db.commit()

        details.update({
          "model_generated": True,
          "download_url": f"/missions/downloads/{dest_name}",
        })
      else:
        details["model_generated"] = False
    except Exception as e:
      details["model_generated"] = False
      details["error"] = str(e)

  return {"completed": completed, "details": details}


@router.get("/downloads/{filename}")
def download_model(filename: str):
  path = Path("downloads") / filename
  if not path.exists():
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
  return FileResponse(path, media_type="model/gltf-binary", filename=filename)