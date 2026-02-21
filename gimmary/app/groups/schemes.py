from pydantic import BaseModel

class GroupCreateRequest(BaseModel):
  team_id: int

class GroupResponse(BaseModel):
  id: int
  team_id: int
  name: str
  leader_id: int
  created_at: str

class GroupUpdateRequest(BaseModel):
  name: str | None
  leader_id: int | None

class UserResponse(BaseModel):
  id: int
  login_id: str
  username: str
  gender: str
  student_id: str
  hakbun: int
  mbti: str

class MissionResponse(BaseModel):
  id: int
  group_id: int
  title: str
  description: str
  status: str
  created_at: str