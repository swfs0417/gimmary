from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from gimmary.database.connection import get_db_session
from gimmary.database.models import Group, GroupMission, Mission, MissionStatus
from gimmary.app.leaderboard.schemas import LeaderboardEntry

leaderboard_router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

@leaderboard_router.get("/{team_id}")
def get_leaderboard(team_id: int, db: Annotated[Session, Depends(get_db_session)]) -> list[LeaderboardEntry]:
  leaderboard_entries = []
  for group in db.query(Group).filter(Group.team_id == team_id).all():
    total_points = (
      db.query(Mission.points)
      .join(GroupMission, GroupMission.mission_id == Mission.id)
      .filter(
        GroupMission.group_id == group.id,
        GroupMission.status == MissionStatus.SUCCESS.value
      )
      .all()
    )
    score = sum(p for (p,) in total_points)
    leaderboard_entries.append(LeaderboardEntry(group_id=group.id, group_name=group.name, points=score))

  leaderboard_entries.sort(key=lambda x: x.points, reverse=True)
  return leaderboard_entries
