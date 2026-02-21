from typing import Annotated
from fastapi import Depends, HTTPException
from gimmary.database.models import User
from gimmary.app.users.schemas import UserCreateRequest, LoginRequest, LoginResponse
from gimmary.app.auth.utils import hash_password, verify_password, issue_token
from gimmary.app.auth.settings import AUTH_SETTINGS
from gimmary.app.users.repositories import UserRepository

class UserService:
    def __init__(self, user_repository: Annotated[UserRepository, Depends()]) -> None:
        self.user_repository = user_repository

    def register_user(self, request: UserCreateRequest):
        hashed_password = hash_password(request.password)
        hakbun = request.student_id[2:4]
        user = User(
            login_id=request.login_id,
            password_hash=hashed_password,
            username=request.username,
            gender=request.gender.value,
            student_id=request.student_id,
            hakbun=hakbun,
            mbti=request.mbti
        )
        return self.user_repository.create_user(user)
    
    def login(self, request: LoginRequest) -> LoginResponse:
        user = self.user_repository.find_by_login_id(request.login_id)
        if not user:
            raise HTTPException(status_code=401, detail='Invalid credentials')
        
        verify_password(request.password, user.password_hash)
        
        access_token = issue_token(
            str(user.id),
            AUTH_SETTINGS.SHORT_SESSION_LIFESPAN,
            AUTH_SETTINGS.ACCESS_TOKEN_SECRET,
        )
        
        return LoginResponse(
            access_token=access_token,
            has_admin_team=self.user_repository.has_admin_team(user.id)
        )