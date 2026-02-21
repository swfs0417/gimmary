from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from gimmary.database.common import Base
from enum import Enum

class UserRole(Enum):
    ADMIN = 'admin'
    PARTICIPANT = 'participant'

class Gender(Enum):
    MALE = 'male'
    FEMALE = 'female'

class FoodType(Enum):
    KOREAN = 'korean'
    CHINESE = 'chinese'
    JAPANESE = 'japanese'
    WESTERN = 'western'
    
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    login_id = Column(String(50), unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    gender = Column(String(10))
    student_id = Column(String(10), unique=True)
    hakbun = Column(Integer)
    mbti = Column(String(4))
    teams = relationship('TeamMember', back_populates='user')
    groups = relationship('GroupMember', back_populates='user')

class Profile(Base):
    __tablename__ = 'profiles'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String(50))
    age = Column(Integer)
    gender = Column(String(10))
    bio = Column(Text)
    etc = Column(Text)

class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    admin_id = Column(Integer, ForeignKey('users.id'))
    auth_code = Column(String(20))
    created_at = Column(DateTime)
    groups = relationship('Group', back_populates='team')
    leaderboard = relationship('Leaderboard', back_populates='team')

class TeamMember(Base):
    __tablename__ = 'team_members'
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    role = Column(String(20), default=UserRole.PARTICIPANT.value)
    food_preference = Column(String(20))
    user = relationship('User', back_populates='teams')
    team = relationship('Team')

class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'))
    name = Column(String(100))
    leader_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime)
    team = relationship('Team', back_populates='groups')
    members = relationship('GroupMember', back_populates='group')
    missions = relationship('Mission', back_populates='group')

class GroupMember(Base):
    __tablename__ = 'group_members'
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    joined_at = Column(DateTime)
    user = relationship('User', back_populates='groups')
    group = relationship('Group', back_populates='members')

class MissionStatus(Enum):
    PENDING = 'pending'
    SUCCESS = 'success'
    FAIL = 'fail'

class Mission(Base):
    __tablename__ = 'missions'
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'))
    title = Column(String(100))
    description = Column(Text)
    status = Column(String(20), default=MissionStatus.PENDING.value)  # 'pending', 'success', 'fail'
    decided_by_admin = Column(Boolean, default=False)
    created_at = Column(DateTime)
    group = relationship('Group', back_populates='missions')

class Leaderboard(Base):
    __tablename__ = 'leaderboards'
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    score = Column(Integer, default=0)
    updated_at = Column(DateTime)
    team = relationship('Team', back_populates='leaderboard')

class MatchType(Enum):
    AUTO = 'auto'
    MANUAL = 'manual'

class MatchStatus(Enum):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'

class MatchRequest(Base):
    __tablename__ = 'match_requests'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    team_id = Column(Integer, ForeignKey('teams.id'))
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=True)
    type = Column(String(20), default=MatchType.AUTO.value)  # 'auto', 'manual'
    target_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    status = Column(String(20), default=MatchStatus.PENDING.value)  # 'pending', 'accepted', 'rejected'
    created_at = Column(DateTime)
