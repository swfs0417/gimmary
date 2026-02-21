from pydantic import BaseModel

class LeaderboardEntry(BaseModel):
  group_id: int
  group_name: str
  points: int