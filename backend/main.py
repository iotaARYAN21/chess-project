from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, user, social
from db.database import init_pool, close_pool

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(social.router)


# ---- Database lifecycle ----
@app.on_event("startup")
async def startup():
    await init_pool()


@app.on_event("shutdown")
async def shutdown():
    await close_pool()