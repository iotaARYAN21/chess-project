from fastapi import APIRouter,HTTPException
from pydantic import BaseModel
from db.queries import get_player_by_email,get_admin_by_email
from utils import create_access_token,decode_token

router = APIRouter(prefix="/auth",tags=["auth"])

class LoginRequest(BaseModel):
    name:str
    email:str
    pwd:str

@router.post("/login")
async def login(data:LoginRequest):
    player = await get_player_by_email(data.email)

    if not player or player["password_hash"]!=data.pwd:
        admin = await get_admin_by_email(data.email)

        if not admin or admin["password_hash"]!=data.pwd:
            raise HTTPException(status_code=400,detail="Invalid email or password")

        # JWT payload
        token_data = {
            "sub": str(admin["id"]),
            "username": admin["username"],
            "role": "sysadmin",
            "admin_level": admin["admin_level"]
        }

        access_token = create_access_token(token_data)

        return {
            "access_token":access_token,
            "token-type":"bearer",
            "role":"sysadmin"
        }

    # JWT payload
    token_data = {
        "sub": str(player["id"]),
        "username": player["username"],
        "role":"player"
    }

    access_token = create_access_token(token_data)

    return {
        "access_token":access_token,
        "token-type":"bearer",
        "user_id":str(player["id"]),
        "username":player["username"],
        "role":"player"
    }

    # print(f"Name: {data.name}")
    # print(f"Email: {data.email}")
    # print(f"Pwd: {data.pwd}")

    # return {
    #     "access_token": "fake-token-123",
    #     "token_type": "bearer"
    # }



# from fastapi import FastAPI,Depends,HTTPException
# from sqlalchemy.orm import Session
# from pydantic import BaseModel

# class UserDate(BaseModel):
#     name:str
#     email:str
#     pwd : str

# class UserResponse(BaseModel):
#     email:str
#     pwd:str

# app = FastAPI()

# def get_db():
#     db = Session()  
#     try:
#         yield db
#     finally:
#         db.close()

# @app.post("/signup",response_model=UserResponse)
# def signup(user_data:UserCreate)


# @app.get('/login')
# def login():
#     return True