from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from gimmary.database.connection import get_db_session
from gimmary.database.models import Team, TeamMember, User
from gimmary.app.auth.utils import get_current_user
from gimmary.app.team.schemas import TeamCreateRequest, TeamMemberResponse, TeamResponse, TeamUpdateRequest

team_router = APIRouter(prefix="/teams", tags=["teams"])

@team_router.post("/")
def create_team(
  request: TeamCreateRequest,
  current_user = Depends(get_current_user),
  db_session = Depends(get_db_session)
) -> TeamResponse:
  if current_user.role != 'admin':
    raise HTTPException(status_code=403, detail="Only admins can create teams")
  
  new_team = Team(
    name=request.name,
    admin_id=current_user.id,
    auth_code=request.auth_code,
    created_at=datetime.now()
  )
  db_session.add(new_team)
  db_session.commit()
  return TeamResponse(
    id=new_team.id,
    name=new_team.name,
    admin_id=new_team.admin_id,
    auth_code=new_team.auth_code,
    created_at=new_team.created_at.isoformat()
  )

@team_router.get("/{team_id}")
def get_team(
  team_id: int,
  current_user = Depends(get_current_user),
  db_session = Depends(get_db_session)
) -> TeamResponse:
  team = db_session.query(Team).filter(Team.id == team_id).first()
  if not team:
    raise HTTPException(status_code=404, detail="Team not found")
  
  # Check if user is part of the team
  membership = db_session.query(TeamMember).filter(
    TeamMember.team_id == team_id,
    TeamMember.user_id == current_user.id
  ).first()
  
  if not membership:
    raise HTTPException(status_code=403, detail="You are not a member of this team")
  
  return TeamResponse(
    id=team.id,
    name=team.name,
    admin_id=team.admin_id,
    auth_code=team.auth_code,
    created_at=team.created_at.isoformat()
  )

@team_router.patch("/{team_id}")
def update_team(
  team_id: int,
  request: TeamUpdateRequest,
  current_user = Depends(get_current_user),
  db_session = Depends(get_db_session)
) -> TeamResponse:
  team = db_session.query(Team).filter(Team.id == team_id).first()
  if not team:
    raise HTTPException(status_code=404, detail="Team not found")
  
  if team.admin_id != current_user.id:
    raise HTTPException(status_code=403, detail="Only the team admin can update the team")
  
  if request.name is not None:
    team.name = request.name
  if request.auth_code is not None:
    team.auth_code = request.auth_code
  db_session.commit()
  
  return TeamResponse(
    id=team.id,
    name=team.name,
    admin_id=team.admin_id,
    auth_code=team.auth_code,
    created_at=team.created_at.isoformat()
  )

@team_router.delete("/{team_id}", status_code=204)
def delete_team(
  team_id: int,
  current_user = Depends(get_current_user),
  db_session = Depends(get_db_session)
):
  team = db_session.query(Team).filter(Team.id == team_id).first()
  if not team:
    raise HTTPException(status_code=404, detail="Team not found")
  
  if team.admin_id != current_user.id:
    raise HTTPException(status_code=403, detail="Only the team admin can delete the team")
  
  db_session.delete(team)
  db_session.commit()
  return

@team_router.get("/{team_id}/members")
def get_team_members(
  team_id: int,
  current_user = Depends(get_current_user),
  db_session = Depends(get_db_session)
) -> list[TeamMemberResponse]:
  team = db_session.query(Team).filter(Team.id == team_id).first()
  if not team:
    raise HTTPException(status_code=404, detail="Team not found")
  
  # Check if user is part of the team
  membership = db_session.query(TeamMember).filter(
    TeamMember.team_id == team_id,
    TeamMember.user_id == current_user.id
  ).first()
  
  if not membership:
    raise HTTPException(status_code=403, detail="You are not a member of this team")
  
  members = db_session.query(TeamMember).filter(TeamMember.team_id == team_id).all()
  
  member_responses = []
  for member in members:
    user = db_session.query(User).filter(User.id == member.user_id).first()
    member_responses.append(TeamMemberResponse(
      id=member.id,
      team_id=member.team_id,
      user_id=member.user_id,
      user_name=user.name if user else "Unknown",
      user_hakbun=user.hakbun if user else "Unknown",
      role=member.role,
      food_preference=member.food_preference
    ))