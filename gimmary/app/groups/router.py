from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from gimmary.app.auth.utils import get_current_user
from gimmary.app.groups.schemes import GroupCreateRequest, GroupResponse, GroupUpdateRequest, UserResponse, MissionResponse
from gimmary.database.connection import get_db_session
from gimmary.database.models import Group, GroupMember, Team, TeamMember, User
from sqlalchemy.orm import Session


groups_router = APIRouter(prefix="/groups", tags=["groups"])

@groups_router.get("/me")
def my_groups(
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_db_session)]
) -> list[GroupResponse]:
    return [
        GroupResponse(
            id=membership.group.id,
            team_id=membership.group.team_id,
            name=membership.group.name,
            leader_id=membership.group.leader_id,
            created_at=membership.group.created_at.isoformat() if membership.group.created_at else ""
        )
        for membership in current_user.groups
    ]

@groups_router.get("/{group_id}")
def get_group(
    group_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_db_session)]
) -> GroupResponse:
    group = db_session.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    member_ids = [m.user_id for m in group.members]
    if current_user.id not in member_ids:
        raise HTTPException(status_code=403, detail="User does not belong to this group")
    return GroupResponse(
        id=group.id,
        team_id=group.team_id,
        name=group.name,
        leader_id=group.leader_id,
        created_at=group.created_at.isoformat() if group.created_at else ""
    )

@groups_router.get("/{group_id}/missions")
def get_group_missions(
    group_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_db_session)]
) -> list[MissionResponse]:
    group = db_session.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    member_ids = [m.user_id for m in group.members]
    if current_user.id not in member_ids:
        raise HTTPException(status_code=403, detail="User does not belong to this group")
    return [
        MissionResponse(
            id=group_mission.mission.id,
            group_id=group_mission.group_id,
            title=group_mission.mission.title,
            description=group_mission.mission.description,
            status=group_mission.status,
            created_at=group_mission.mission.created_at.isoformat() if group_mission.mission.created_at else None
        )
        for group_mission in group.group_missions

    ]
    
@groups_router.get("/{group_id}/members")
def get_group_members(
    group_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_db_session)]
) -> list[UserResponse]:
    group = db_session.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return [
        UserResponse(
            id=member.id,
            login_id=member.user.login_id,
            username=member.user.username,
            gender=member.user.gender,
            student_id=member.user.student_id,
            hakbun=member.user.hakbun,
            mbti=member.user.mbti
        )
        for member in group.members
    ]
@groups_router.post("/{group_id}/members")
def add_group_member(
    group_id: int,
    user_id: int,
    db_session: Annotated[Session, Depends(get_db_session)]
):
    group = db_session.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    user = db_session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user in group.members:
        raise HTTPException(status_code=400, detail="User is already a member of the group")
    group.members.append(user)
    db_session.add(group)
    db_session.commit()

@groups_router.delete("/{group_id}/members/{user_id}")
def remove_group_member(
    group_id: int,
    user_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_db_session)]
):
    group = db_session.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if group.leader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the group leader can remove members")
    user = db_session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user not in group.members:
        raise HTTPException(status_code=400, detail="User is not a member of the group")
    group.members.remove(user)
    db_session.add(group)
    db_session.commit() 

@groups_router.post("/")
def create_group(
    request: GroupCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_db_session)]
) -> list[GroupResponse]:
    members = db_session.query(TeamMember).filter(TeamMember.team_id == request.team_id and not (member.user_id for member in Group.members)).all()
    existing_member_ids = set()
    for group in db_session.query(Group).filter(Group.team_id == request.team_id).all():
        for member in group.members:
            existing_member_ids.add(member.id)
    members = [member for member in members if member.user_id not in existing_member_ids]
    teams = [[] for _ in range(len(members)//4+1)]
    for i, member in enumerate(members):
        teams[i//4].append(member)
    for i, members in enumerate(teams):
        if not members:
          continue
        group = Group(
            team_id=request.team_id,
            name=f"{len(db_session.query(Group).filter(Group.team_id == request.team_id).all())+1}조",
            leader_id=members[0].user_id,
        )
        db_session.add(group)
        db_session.commit()
        db_session.refresh(group)
        for member in members:
            group_member = GroupMember(group_id=group.id, user_id=member.user_id)
            db_session.add(group_member)
        db_session.commit()
    groups = db_session.query(Group).filter(Group.team_id == request.team_id).all()
    return [
        GroupResponse(
            id=group.id,
            team_id=group.team_id,
            name=group.name,
            leader_id=group.leader_id,
            created_at=group.created_at.isoformat() if group.created_at else ''
        )
        for group in groups
    ]

@groups_router.patch("/{group_id}")
def update_group(
    group_id: int,
    request: GroupUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_db_session)]
) -> GroupResponse:
    group = db_session.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if group.leader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the group leader can update the group")

    if request.leader_id is not None:
        new_leader = db_session.query(User).filter(User.id == request.leader_id).first()
        if not new_leader:
            raise HTTPException(status_code=404, detail="New leader user not found")
        member_ids = [m.user_id for m in group.members]
        if new_leader.id not in member_ids:
            raise HTTPException(status_code=400, detail="New leader must be a member of the group")
        group.leader_id = request.leader_id
    if request.name is not None:
        group.name = request.name

    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    return GroupResponse(
        id=group.id,
        team_id=group.team_id,
        name=group.name,
        leader_id=group.leader_id,
        created_at=group.created_at.isoformat() if group.created_at else ""
    )

@groups_router.delete("/{group_id}", status_code=204)
def delete_group(
    group_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_db_session)]
):
    group = db_session.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if group.leader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the group leader can delete the group")
    db_session.delete(group)
    db_session.commit()