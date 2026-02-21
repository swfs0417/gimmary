from pydantic import BaseModel
from typing import List
import random
import string

def create_auth_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

class TeamCreateRequest(BaseModel):
    name: str

class TeamJoinRequest(BaseModel):
    auth_code: str

class TeamUpdateRequest(BaseModel):
    name: str | None
    auth_code: str | None

class TeamResponse(BaseModel):
    id: int
    name: str
    admin_id: int
    auth_code: str
    created_at: str

class TeamMemberResponse(BaseModel):
    id: int
    team_id: int
    user_id: int
    user_name: str
    user_student_id: str
    user_hakbun: int
    role: str

class MyTeamResponse(BaseModel):
    id: int
    name: str
    admin_id: int
    auth_code: str
    created_at: str
    my_role: str