from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from gimmary.database.connection import get_db_session
from gimmary.database.models import User

class UserRepository:
    def __init__(self, session: Annotated[Session, Depends(get_db_session)]) -> None:
        self.session = session

    def create_user(self, user: User) -> User:
        self.session.add(user)
        self.session.commit()
        return user