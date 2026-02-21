from pydantic import BaseModel

# ── Mission (팀 레벨 정의) ──────────────────────────

class MissionCreateRequest(BaseModel):
  team_id: int
  title: str
  description: str
  points: int = 0

class MissionUpdateRequest(BaseModel):
  title: str | None = None
  description: str | None = None
  points: int | None = None

class MissionResponse(BaseModel):
  id: int
  team_id: int
  title: str
  description: str
  points: int
  created_at: str

# ── GroupMission (그룹별 달성 상태) ─────────────────

class GroupMissionUpdateRequest(BaseModel):
  status: str | None = None

class GroupMissionResponse(BaseModel):
  id: int
  mission_id: int
  group_id: int
  status: str