from pydantic import BaseModel
from gimmary.database.models import Gender 

class UserCreateRequest(BaseModel):
    login_id: str
    password: str
    username: str
    gender: Gender
    student_id: str
    mbti: str

class LoginRequest(BaseModel):
    login_id: str
    password: str

class LoginResponse(BaseModel):
    access_token: str