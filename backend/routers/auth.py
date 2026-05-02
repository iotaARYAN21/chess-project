from fastapi import APIRouter,HTTPException
from pydantic import BaseModel
from db.queries import get_player_by_email
import jwt
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM")

def create_access_token(user_id: str) -> str:
    payload = {
        "sub": user_id
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

router = APIRouter(prefix="/auth",tags=["auth"])

class LoginRequest(BaseModel):
    name:str
    email:str
    pwd:str

@router.post("/login")
async def login(data: LoginRequest):
    player = await get_player_by_email(data.email)

    if not player or player["password_hash"] != data.pwd:
        raise HTTPException(
            status_code=400,
            detail="Invalid email or password"
        )

    token = create_access_token(str(player["id"]))

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": str(player["id"]),
        "username": player["username"]
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