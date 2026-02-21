from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from gimmary.database.connection import get_db_session
from gimmary.database.models import Team, TeamMember, User, UserRole, Mission
from gimmary.app.auth.utils import get_current_user
from gimmary.app.team.schemas import TeamCreateRequest, TeamJoinRequest, TeamMemberResponse, TeamResponse, TeamUpdateRequest, MyTeamResponse, create_auth_code
from gimmary.app.missions.schemes import MissionResponse

team_router = APIRouter(prefix="/teams", tags=["teams"])

@team_router.post("/", response_model=TeamResponse)
def create_team(
    request: TeamCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_db_session)]
):
    # 팀 이름 중복 체크
    existing_team = db_session.query(Team).filter(Team.name == request.name).first()
    if existing_team:
        raise HTTPException(status_code=400, detail="Team name already exists")
    
    # auth_code 생성
    auth_code = create_auth_code()
    
    # 팀 생성
    team = Team(
        name=request.name,
        admin_id=current_user.id,
        auth_code=auth_code,
        created_at=datetime.now()
    )
    db_session.add(team)
    db_session.commit()
    db_session.refresh(team)
    
    # 팀 생성자를 관리자로 팀 멤버에 추가
    team_member = TeamMember(
        team_id=team.id,
        user_id=current_user.id,
        role=UserRole.ADMIN.value
    )
    db_session.add(team_member)
    db_session.commit()
    
    return TeamResponse(
        id=team.id,
        name=team.name,
        admin_id=team.admin_id,
        auth_code=team.auth_code,
        created_at=team.created_at.isoformat()
    )

@team_router.get("/me", response_model=list[MyTeamResponse])
def get_my_teams(
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_db_session)]
):
    memberships = (
        db_session.query(TeamMember)
        .filter(TeamMember.user_id == current_user.id)
        .all()
    )

    return [
        MyTeamResponse(
            id=m.team.id,
            name=m.team.name,
            admin_id=m.team.admin_id,
            auth_code=m.team.auth_code,
            created_at=m.team.created_at.isoformat(),
            my_role=m.role
        )
        for m in memberships
    ]

@team_router.post("/join", response_model=TeamMemberResponse)
def join_team(
    request: TeamJoinRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_db_session)]
):
    # auth_code로 팀 찾기
    team = db_session.query(Team).filter(Team.auth_code == request.auth_code).first()
    if not team:
        raise HTTPException(status_code=404, detail="Invalid auth code")
    
    # 이미 팀에 가입되어 있는지 확인
    existing_member = db_session.query(TeamMember).filter(
        TeamMember.team_id == team.id,
        TeamMember.user_id == current_user.id
    ).first()
    if existing_member:
        raise HTTPException(status_code=400, detail="Already a member of this team")
    
    # 팀에 가입
    team_member = TeamMember(
        team_id=team.id,
        user_id=current_user.id,
        role=UserRole.PARTICIPANT.value
    )
    db_session.add(team_member)
    db_session.commit()
    db_session.refresh(team_member)
    
    return TeamMemberResponse(
        id=team_member.id,
        team_id=team_member.team_id,
        user_id=current_user.id,
        user_name=current_user.username,
        user_student_id=current_user.student_id,
        user_hakbun=current_user.hakbun,
        role=team_member.role
    )

@team_router.get("/{team_id}/missions", response_model=list[MissionResponse])
def get_team_missions(
    team_id: int,
    db_session: Annotated[Session, Depends(get_db_session)]
):
    missions = db_session.query(Mission).filter(Mission.team_id == team_id).all()

    return [
        MissionResponse(
            id=m.id,
            team_id=m.team_id,
            title=m.title,
            description=m.description,
            points=m.points,
            created_at=m.created_at.isoformat() if m.created_at else "",
            model_url=m.model_url,
        )
        for m in missions
    ]

@team_router.get("/{team_id}/members", response_model=list[TeamMemberResponse])
def get_team_members(
    team_id: int,
    db_session: Annotated[Session, Depends(get_db_session)]
):
    team_members = db_session.query(TeamMember).filter(TeamMember.team_id == team_id).all()
    
    if not team_members:
        raise HTTPException(status_code=404, detail="Team not found or has no members")
    return [
        TeamMemberResponse(
            id=m.id,
            team_id=m.team_id,
            user_id=m.user_id,
            user_name=m.user.username,
            user_student_id=m.user.student_id,
            user_hakbun=m.user.hakbun,
            role=m.role
        )
        for m in team_members
    ]
