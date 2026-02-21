from pydantic import BaseModel

class GroupCreateRequest(BaseModel):
  team_id: int
  name: str
  leader_id: int

class GroupResponse(BaseModel):
  id: int
  team_id: int
  name: str
  leader_id: int
  created_at: str

class GroupUpdateRequest(BaseModel):
  name: str | None
  leader_id: int | None