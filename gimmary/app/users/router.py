from fastapi import APIRouter, Depends
from typing import Annotated
from gimmary.app.users.schemas import UserCreateRequest, LoginRequest, LoginResponse
from gimmary.app.users.services import UserService

user_router = APIRouter(prefix="/users", tags=["users"])

@user_router.post("/register")
def register_user(
  request: UserCreateRequest,
  user_servcie: Annotated[UserService, Depends()]
):
    user_servcie.register_user(request)
    return {"message": "User registered successfully"}

@user_router.post("/login", response_model=LoginResponse)
def login_user(
    request: LoginRequest,
    user_service: Annotated[UserService, Depends()]
) -> LoginResponse:
    return user_service.login(request)