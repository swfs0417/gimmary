from typing import Annotated
from fastapi import Depends
from gimmary.database.models import User
from gimmary.app.users.schemas import UserCreateRequest
from gimmary.app.auth.utils import hash_password
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