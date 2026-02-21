from fastapi import APIRouter, Depends
from typing import Annotated
from gimmary.app.users.schemas import UserCreateRequest
from gimmary.app.users.services import UserService

user_router = APIRouter(prefix="/users", tags=["users"])

@user_router.post("/register")
def register_user(
  request: UserCreateRequest,
  user_servcie: Annotated[UserService, Depends()]
):
    user_servcie.register_user(request)
    return {"message": "User registered successfully"}