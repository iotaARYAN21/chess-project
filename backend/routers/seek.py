from fastapi import APIRouter,HTTPException
from pydantic import BaseModel
import uuid
from db.queries import get_account_by_username,create_match,get_user_stats_by_mode
# from database import DBSession

router = APIRouter(prefix='/api')
class BotMatchRequest(BaseModel):
    game_mode:str
    bot_username:str
    userid:uuid.UUID
    time_control_id:uuid.UUID

@router.post('/seek')
async def create_bot_match(request: BotMatchRequest):
    """
    Creates an instant match by querying the engine from the database.
    """
    bot_account = await get_account_by_username(request.bot_username)
    if not bot_account:
        raise HTTPException(status_code=404, detail="Engine account not found in database")
    
    try:
        user_stats = await get_user_stats_by_mode(request.userid) # TODO -> the function should accept id instead of username
        user_elo = user_stats[2] # as returns a list and according to relational model , elo is on 2nd index
        new_game_id = await create_match( # returns uniq id
            white_id = request.userid,
            black_id=bot_account["id"],
            time_control_id=request.time_control_id,
            white_elo=user_elo,
            black_elo=3200  #TODO defaulting elo rating of engine to 3200
        )
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Failed to create a match ,error: {e}")
    
    return {
        "status":"matched",
        "game_id":str(new_game_id),
        "opponent_name":bot_account["username"],
        "opponent_id":str(bot_account["id"])
    }


# @router.post('/seek')
# async def create_bot_match(request: BotMatchRequest, db=Depends(get_db)):
#     """
#     Creates an instant match by querying the engine from the database.
#     """
    
#     # 2. Query ACCOUNT table to find the bot
#     # This is pseudo-code depending on if you use SQLAlchemy, asyncpg, etc.
#     # SQL equivalent: SELECT id, username FROM account WHERE username = 'GM_Magnus90' AND player_type = 'engine'
    
#     bot_account = db.execute(
#         "SELECT id, username FROM ACCOUNT WHERE username = :username", 
#         {"username": request.bot_username}
#     ).fetchone()

#     if not bot_account:
#         raise HTTPException(status_code=404, detail="Engine account not found in database")
    
#     new_game_id = str(uuid.uuid4())
    
#     # 3. Database Logic Goes Here:
#     # INSERT INTO MATCH (id, status, fen, black_id...) 
#     # VALUES (new_game_id, 'ongoing', 'rnbqkbnr/...', bot_account.id) 
    
#     # 4. Return the actual DB data to the frontend
#     return {
#         "status": "matched",
#         "game_id": new_game_id,
#         "opponent_name": bot_account.username,
#         "opponent_id": str(bot_account.id)
#     }