from fastapi import APIRouter,HTTPException,Depends
from pydantic import BaseModel
import uuid
# from database import DBSession

router = APIRouter(prefix='/api')
class BotMatchRequest(BaseModel):
    game_mode:str
    bot_username:str

async def get_db():
    # db = DBSession()
    db=''
    try:
        yield db
    finally:
        # db.close()
        return  # remove this line after completing dbsession logic
    
@router.post('/seek')
async def create_bot_match(request: BotMatchRequest, db=Depends(get_db)):
    """
    Creates an instant match by querying the engine from the database.
    """
    
    # 2. Query ACCOUNT table to find the bot
    # This is pseudo-code depending on if you use SQLAlchemy, asyncpg, etc.
    # SQL equivalent: SELECT id, username FROM account WHERE username = 'GM_Magnus90' AND player_type = 'engine'
    
    bot_account = db.execute(
        "SELECT id, username FROM ACCOUNT WHERE username = :username", 
        {"username": request.bot_username}
    ).fetchone()

    if not bot_account:
        raise HTTPException(status_code=404, detail="Engine account not found in database")
    
    new_game_id = str(uuid.uuid4())
    
    # 3. Database Logic Goes Here:
    # INSERT INTO MATCH (id, status, fen, black_id...) 
    # VALUES (new_game_id, 'ongoing', 'rnbqkbnr/...', bot_account.id) 
    
    # 4. Return the actual DB data to the frontend
    return {
        "status": "matched",
        "game_id": new_game_id,
        "opponent_name": bot_account.username,
        "opponent_id": str(bot_account.id)
    }