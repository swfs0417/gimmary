from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from gimmary.database.connection import get_db_session
from gimmary.database.models import Group, MissionStatus, User
from gimmary.app.auth.utils import get_current_user
from gimmary.app.leaderboard.schemas import LeaderboardEntry

leaderboard_router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

@leaderboard_router.get("/{team_id}")
def get_leaderboard(team_id: int, db: Annotated[Session, Depends(get_db_session)]) -> list[LeaderboardEntry]:
  leaderboard_entries = []
  for group in db.query(Group).filter(Group.team_id == team_id).all():
    success_count = len([mission for mission in group.missions if mission.status == MissionStatus.SUCCESS.value])
    leaderboard_entries.append(LeaderboardEntry(group_id = group.id, group_name=group.name, points=success_count))
  leaderboard_entries.sort(key=lambda x: x.points, reverse=True)
  return leaderboard_entries
