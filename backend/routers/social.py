from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/social", tags=["social"])

# MOCK DB 

friend_requests = []
friends = {}
followers = {}

# HELPERS 

def get_current_user():
    return "murali"  # TODO replace with auth


# MODELS 

class FriendRequestBody(BaseModel):
    to_username: str


class FollowBody(BaseModel):
    target_username: str


# FRIEND REQUESTS 

@router.post("/friend-request")
def send_friend_request(data: FriendRequestBody):
    from_user = get_current_user()

    if from_user == data.to_username:
        raise HTTPException(status_code=400, detail="Cannot friend yourself")

    request = {
        "id": len(friend_requests) + 1,
        "from": from_user,
        "to": data.to_username,
        "status": "pending"
    }

    friend_requests.append(request)

    return {"message": "Friend request sent", "request": request}


@router.get("/friend-requests")
def get_friend_requests():
    user = get_current_user()

    return [
        r for r in friend_requests
        if r["to"] == user and r["status"] == "pending"
    ]


@router.post("/friend-request/{req_id}/accept")
def accept_request(req_id: int):
    user = get_current_user()

    for r in friend_requests:
        if r["id"] == req_id:
            if r["to"] != user:
                raise HTTPException(status_code=403)

            r["status"] = "accepted"

            friends.setdefault(user, []).append(r["from"])
            friends.setdefault(r["from"], []).append(user)

            return {"message": "Accepted"}

    raise HTTPException(status_code=404)


@router.post("/friend-request/{req_id}/decline")
def decline_request(req_id: int):
    user = get_current_user()

    for r in friend_requests:
        if r["id"] == req_id:
            if r["to"] != user:
                raise HTTPException(status_code=403)

            r["status"] = "declined"
            return {"message": "Declined"}

    raise HTTPException(status_code=404)


@router.delete("/friend-request/{req_id}")
def cancel_request(req_id: int):
    user = get_current_user()

    for r in friend_requests:
        if r["id"] == req_id:
            if r["from"] != user:
                raise HTTPException(status_code=403)

            r["status"] = "cancelled"
            return {"message": "Cancelled"}

    raise HTTPException(status_code=404)


@router.get("/friends")
def get_friends():
    user = get_current_user()
    return friends.get(user, [])

@router.post("/follow")
def follow_user(data: FollowBody):
    user = get_current_user()

    if user == data.target_username:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    followers.setdefault(data.target_username, set()).add(user)

    return {"message": "Followed"}


@router.delete("/follow/{username}")
def unfollow_user(username: str):
    user = get_current_user()

    if username in followers:
        followers[username].discard(user)

    return {"message": "Unfollowed"}