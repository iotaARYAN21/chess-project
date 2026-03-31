from fastapi import FastAPI,Depends,HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

class UserDate(BaseModel):
    name:str
    email:str
    pwd : str

class UserResponse(BaseModel):
    email:str
    pwd:str

app = FastAPI()

def get_db():
    db = Session()  
    try:
        yield db
    finally:
        db.close()

# @app.post("/signup",response_model=UserResponse)
# def signup(user_data:UserCreate)


# @app.get('/login')
# def login():
#     return True