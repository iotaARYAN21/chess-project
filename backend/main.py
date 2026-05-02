from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from db.database import init_pool, close_pool, get_pool
from db.queries import get_account_by_id
from routers import auth, user, social, seek, match, mode
from utils import get_current_user, get_user_id
import uuid


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    yield
    await close_pool()


app = FastAPI(lifespan=lifespan)


@app.get("/health", include_in_schema=False)
async def health_check():
    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute("SELECT 1")
        return {"status": "healthy", "database": "up"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 500


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/me")
async def get_me(user_id: uuid.UUID = Depends(get_user_id)):
    account = await get_account_by_id(user_id)
    if not account:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": account["username"]}

app.include_router(auth.router)
app.include_router(mode.router)
app.include_router(match.router, dependencies=[Depends(get_user_id)])

app.include_router(user.router, dependencies=[Depends(get_current_user)])
app.include_router(social.router, dependencies=[Depends(get_current_user)])
app.include_router(seek.router, dependencies=[Depends(get_current_user)])
