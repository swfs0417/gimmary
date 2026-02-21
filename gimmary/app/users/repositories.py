from typing import Annotated, Optional
from fastapi import Depends
from sqlalchemy.orm import Session
from gimmary.database.connection import get_db_session
from gimmary.database.models import User, TeamMember, UserRole

class UserRepository:
    def __init__(self, session: Annotated[Session, Depends(get_db_session)]) -> None:
        self.session = session

    def create_user(self, user: User) -> User:
        self.session.add(user)
        self.session.commit()
        return user
    
    def find_by_login_id(self, login_id: str) -> Optional[User]:
        return self.session.query(User).filter(User.login_id == login_id).first()

    def has_admin_team(self, user_id: int) -> bool:
        return self.session.query(TeamMember).filter(
            TeamMember.user_id == user_id,
            TeamMember.role == UserRole.ADMIN.value
        ).first() is not None