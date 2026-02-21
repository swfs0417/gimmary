from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from gimmary.app.auth.utils import get_current_user
from gimmary.app.groups.schemes import GroupCreateRequest, GroupResponse, GroupUpdateRequest
from gimmary.app.missions.schemes import MissionResponse
from gimmary.database.connection import get_db_session
from gimmary.database.models import Group, User
from sqlalchemy.orm import Session


groups_router = APIRouter(prefix="/groups", tags=["groups"])

@groups_router.get("/me")
def my_groups(
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_db_session)]
) -> list[GroupResponse]:
    return [
        GroupResponse(
            id=group.id,
            name=group.name,
            admin_id=group.admin_id,
            auth_code=group.auth_code,
            created_at=group.created_at.isoformat() if group.created_at else None
        )
        for group in current_user.groups
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
    if group not in current_user.groups:
        raise HTTPException(status_code=403, detail="User does not belong to this group")
    return GroupResponse(
        id=group.id,
        name=group.name,
        admin_id=group.admin_id,
        auth_code=group.auth_code,
        created_at=group.created_at.isoformat() if group.created_at else None
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
    if group not in current_user.groups:
        raise HTTPException(status_code=403, detail="User does not belong to this group")
    return [
        MissionResponse(
            id=mission.id,
            group_id=mission.group_id,
            title=mission.title,
            description=mission.description,
            status=mission.status,
            decided_by_admin=bool(mission.decided_by_admin),
            created_at=mission.created_at.isoformat() if mission.created_at else None
        )
        for mission in group.missions
    ]
    
@groups_router.get("/{group_id}/members")
def get_group_members(
    group_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_db_session)]
) -> list[User]:
    group = db_session.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if group not in current_user.groups:
        raise HTTPException(status_code=403, detail="User does not belong to this group")
    return group.members
@groups_router.post("/{group_id}/members")
def add_group_member(
    group_id: int,
    user_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_db_session)]
):
    group = db_session.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if group.leader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the group leader can add members")
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
) -> GroupResponse:
    group = Group(
        team_id=request.team_id,
        name=request.name,
        leader_id=current_user.id,
        created_at=request.created_at
    )
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    return GroupResponse(
        id=group.id,
        name=group.name,
        admin_id=group.admin_id,
        auth_code=group.auth_code,
        created_at=group.created_at.isoformat() if group.created_at else None
    )

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
        if new_leader not in group.members:
            raise HTTPException(status_code=400, detail="New leader must be a member of the group")
        group.leader_id = request.leader_id
    if request.name is not None:
        group.name = request.name

    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    return GroupResponse(
        id=group.id,
        name=group.name,
        admin_id=group.admin_id,
        auth_code=group.auth_code,
        created_at=group.created_at.isoformat() if group.created_at else None
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