from pydantic import BaseModel

def create_auth_code():
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

class TeamCreateRequest(BaseModel):
    name: str
    admin_id: int
    auth_code: str = create_auth_code()

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
    food_preference: str