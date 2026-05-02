from fastapi import APIRouter, HTTPException,Depends
from pydantic import BaseModel
import uuid
from utils import get_current_user

from db.queries import (
    get_account_by_username,
    send_friend_request,
    get_pending_friend_requests,
    respond_to_friend_request,
    add_friendship,
    remove_friendship,
    get_friends,
    follow_user,
    unfollow_user,
    get_friend_request_by_id
)

router = APIRouter(prefix="/social", tags=["social"])


# def get_current_user():
#     return "murali"  # TODO replace with auth

    
class FriendRequestBody(BaseModel):
    to_username: str


class FollowBody(BaseModel):
    target_username: str


# FRIEND REQUEST 

@router.post("/friend-request")
async def send_request(data: FriendRequestBody,from_user = Depends(get_current_user)):
    if from_user == data.to_username:
        raise HTTPException(status_code=400, detail="Cannot friend yourself")

    from_acc = await get_account_by_username(from_user)
    to_acc = await get_account_by_username(data.to_username)

    if not to_acc:
        raise HTTPException(status_code=404, detail="Target user not found")

    req_id = await send_friend_request(from_acc["id"], to_acc["id"])

    return {"message": "Friend request sent", "request_id": str(req_id)}


@router.get("/friend-requests")
async def get_requests(user = Depends(get_current_user)):
    rows = await get_pending_friend_requests(user)

    return [dict(r) for r in rows]


@router.post("/friend-request/{req_id}/accept")
async def accept_request(req_id: str,user = Depends(get_current_user)):
    req_uuid = uuid.UUID(req_id) 

    req = await get_friend_request_by_id(req_uuid)

    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if req["to_username"] != user:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Update status
    await respond_to_friend_request(req_uuid, "accepted")

    # Create friendship
    await add_friendship(req["from_user"], req["to_user"])

    return {"message": "Accepted"}


@router.post("/friend-request/{req_id}/decline")
async def decline_request(req_id: str):
    req_uuid = uuid.UUID(req_id)
    await respond_to_friend_request(req_uuid, "declined")
    return {"message": "Declined"}


@router.delete("/friend-request/{req_id}")
async def cancel_request(req_id: str):
    req_uuid = uuid.UUID(req_id)
    await respond_to_friend_request(req_uuid, "cancelled")
    return {"message": "Cancelled"}


#  FRIENDS 

@router.get("/friends")
async def get_friends_list(user = Depends(get_current_user)):
    rows = await get_friends(user)

    return [dict(r) for r in rows]

@router.delete("/friends/{username}")
async def remove_friend(username: str,current_user = Depends(get_current_user)):
    user_acc = await get_account_by_username(current_user)
    target_acc = await get_account_by_username(username)

    if not target_acc:
        raise HTTPException(status_code=404, detail="User not found")

    await remove_friendship(user_acc["id"], target_acc["id"])

    return {"message": "Friend removed"}

# FOLLOW

@router.post("/follow")
async def follow(data: FollowBody,user = Depends(get_current_user)):
    if user == data.target_username:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    user_acc = await get_account_by_username(user)
    target_acc = await get_account_by_username(data.target_username)

    if not target_acc:
        raise HTTPException(status_code=404, detail="User not found")

    await follow_user(user_acc["id"], target_acc["id"])

    return {"message": "Followed"}


@router.delete("/follow/{username}")
async def unfollow(username: str,user = Depends(get_current_user)):
    user_acc = await get_account_by_username(user)
    target_acc = await get_account_by_username(username)

    if not target_acc:
        raise HTTPException(status_code=404, detail="User not found")

    await unfollow_user(user_acc["id"], target_acc["id"])

    return {"message": "Unfollowed"}