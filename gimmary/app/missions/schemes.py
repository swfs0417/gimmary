from pydantic import BaseModel

class MissionCreateRequest(BaseModel):
  group_id: int
  title: str
  description: str

class MissionUpdateRequest(BaseModel):
  title: str | None
  description: str | None
  status: str | None
  decided_by_admin: bool | None

class MissionResponse(BaseModel):
  id: int
  group_id: int
  title: str
  description: str
  status: str
  decided_by_admin: bool
  created_at: str