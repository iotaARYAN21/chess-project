from pydantic import BaseModel, ConfigDict, ValidationError
from fastapi import APIRouter, Depends, HTTPException
from starlette import status
import uuid
from utils import get_user_id, calculate_elos
import chess, math
from http import HTTPStatus
from datetime import datetime, timezone
from db.queries import get_match_by_id, get_match_state_by_id, get_time_control_by_id, \
    call_handle_match_move, call_handle_timeout
from typing import Literal, Optional
from models.match import MatchModel, MatchStateModel
from models.game import TimeControlModel
from schemas.match.requests import MatchMoveRequestModel
from schemas.match.responses import MatchMoveResponseModel, MatchFetchResponseModel
from db.database import get_pool

router = APIRouter(
    prefix="/match",
    tags=["match"]
)


# def get_user_id():
#     return uuid.UUID("a1000000-0000-0000-0000-000000000001")

@router.get(
    path="/{match_id}",
    # response_model= MatchFetchResponseModel # TODO
)
async def match_fetch_info(
    match_id: uuid.UUID,
    user_id:    str = Depends(get_user_id),
):
    pass

@router.post(
    path="/{match_id}/move",
    response_model= MatchMoveResponseModel
)
async def match_make_move(
    match_id:   uuid.UUID,
    request:    MatchMoveRequestModel,
    user_id:    str = Depends(get_user_id),
):
    move_played_at = datetime.now(timezone.utc)

    # FETCH AND VALIDATE MATCH
    match_record = await get_match_by_id(match_id)
    if not match_record: 
        raise HTTPException(HTTPStatus.NOT_FOUND, "`match` record not found")
    # print(dict(match_record))
    try:
        match : MatchModel = MatchModel.model_validate(dict(match_record))
    except ValidationError as e:
        raise HTTPException(HTTPStatus.INTERNAL_SERVER_ERROR,f"Data integrity error: `match` record corrupted {e}")

    # AUTHORIZATION CHECKS
    is_white = match.white_id is not None and user_id == match.white_id
    is_black = match.black_id is not None and user_id == match.black_id
    if not (is_white or is_black):
        raise HTTPException(HTTPStatus.FORBIDDEN, "You are not a player in this match")
    
    if match.status != 'active' :
        raise HTTPException(HTTPStatus.BAD_REQUEST, "Match is not active")
    
    # FETCH TIME CONTROL
    time_control_record = await get_time_control_by_id(match.time_control_id)
    if not time_control_record: 
        raise HTTPException(HTTPStatus.NOT_FOUND, f"`time_control` record not found")
    
    try:
        time_control : TimeControlModel = TimeControlModel.model_validate(dict(time_control_record))
    except ValidationError as e:
        raise HTTPException(HTTPStatus.INTERNAL_SERVER_ERROR,f"Data integrity error: `time_control` record corrupted {e}")
    
    # FETCH MATCH STATE
    match_state_record = await get_match_state_by_id(match_id)
    if not match_state_record: 
        raise HTTPException(HTTPStatus.INTERNAL_SERVER_ERROR, "`match_state` record not found - trigger error")
    
    try:
        match_state : MatchStateModel = MatchStateModel.model_validate(dict(match_state_record))
    except ValidationError as e:
        raise HTTPException(HTTPStatus.INTERNAL_SERVER_ERROR,f"Data integrity error: `match_state` record corrupted {e}")
    

    # LOAD AND VALIDATE BOARD STATE
    try:
        board = chess.Board(match_state.fen)
        if not board.is_valid():
            raise HTTPException(HTTPStatus.INTERNAL_SERVER_ERROR, f"Corrupt FEN")
    except Exception as err:
        raise HTTPException(HTTPStatus.INTERNAL_SERVER_ERROR, f"Invalid FEN: {err}")

    # VALIDATE PLAYER TURN
    player_color = 'white' if is_white else 'black'
    opponent_color = 'black' if is_white else 'white'
    if board.turn != (player_color == 'white'):
        raise HTTPException(HTTPStatus.BAD_REQUEST, "Not your turn")
    
    # VALIDATE MOVE
    try:
        move = chess.Move.from_uci(request.uci)
    except chess.InvalidMoveError:
        raise HTTPException(HTTPStatus.BAD_REQUEST, "Invalid UCI move format")
    
    if move not in board.legal_moves:
        raise HTTPException(HTTPStatus.BAD_REQUEST, "Illegal move")
    # store san before pushing
    san_move = board.san(move)

    
    # CALCULATE TIME ELAPSED
    elapsed_ms = int ((move_played_at - match_state.turn_started_at).total_seconds() * 1000)
    # in case of premoves or desynchronization
    if elapsed_ms < 0: 
        elapsed_ms = 0


    # CALCULATE REMAINING TIME
    times = {
        "white": match_state.white_time_remaining_ms,
        "black": match_state.black_time_remaining_ms
    }

    times[player_color] -= elapsed_ms

    status, result, ended_at = 'active', None, None
    istimeout = True if times[player_color] < 0 else False
    if istimeout: # timeout dont push the move
        times[player_color] = 0  # Clamp to zero
        status, ended_at = 'completed', move_played_at
        
        opp_color_const = chess.BLACK if is_white else chess.WHITE
        if board.has_insufficient_material(opp_color_const):
            result = "draw" # Timeout vs Insufficient Material
        else:
            result = opponent_color

    else: # if no timeout and move succesful then increment (sec to ms)
        times[player_color] += time_control.incr_time * 1000 
        board.push(move)

        outcome = board.outcome(claim_draw=False)
        if outcome:
            status, ended_at = 'completed', move_played_at
            if outcome.winner == chess.WHITE:
                result = "white"
            elif outcome.winner == chess.BLACK:
                result = "black"
            else:
                result = "draw"

    white_remaining_ms = times["white"]
    black_remaining_ms = times["black"]

     # CALCULATE ELO CHANGES
    if status == 'completed' and result:
        new_white_elo, new_black_elo = calculate_elos(
            match.white_elo_initial,
            match.black_elo_initial,
            result
        )
        white_elo_shift = new_white_elo - match.white_elo_initial
        black_elo_shift = new_black_elo - match.black_elo_initial
    else:
        white_elo_shift = 0
        black_elo_shift = 0

    # TODO: also need to add draw-offered-by
    # also note that i have to run a cron job to handle timeout where no move was made
    # i have to handle timeout where player reconnects so a get request is made in that case also i can handle it
    # maybe i can have a claim-timeout endpoint to handle this
    
    if istimeout:
        # TODO: create a transaction function for this
        # await call_handle_timeout(
        #     match_id,
        #     match_state.move_number,
        #     white_remaining_ms,
        #     black_remaining_ms,
        #     elapsed_ms,
        #     # status,
        #     result,
        #     ended_at,
        #     white_elo_diff,
        #     black_elo_diff
        # )
        pass
    else:
        await call_handle_match_move(
            match_id,
            match_state.move_number + 1,
            request.uci,
            board.fen(),
            white_remaining_ms,
            black_remaining_ms,
            status,
            move_played_at,
            result,
            ended_at,
            white_elo_shift,
            black_elo_shift
        )
        

    # 9) Return enough info for frontend clock sync
    return \
        MatchMoveResponseModel(
        fen=board.fen() if not istimeout else match_state.fen,
        status=status,
        result=result,
        uci=request.uci if not istimeout else None,
        san=san_move if not istimeout else None,
        server_now=move_played_at,
        turn_started_at=move_played_at,
        white_time_remaining_ms=white_remaining_ms,
        black_time_remaining_ms=black_remaining_ms,
    )
            
    


# @router.post(
#     path="/match/{match_id}/resign"
# )
# async def match_resign(
#     match_id: str,
#     user_id = Depends(get_user_id),
# ):
#     match_id = str(match_id)
#     match = db_get_match(match_id)
#     """
#     select * from match where match_id = $1
#     """
#     if not match: 
#         raise HTTPException(404, "Match not found")
    
#     if user_id not in [match.white_id, match.black_id]:
#         raise HTTPException(403, "Player not eligible")
    
#     if match.status != 'active':
#         raise HTTPException(400, "Match not active")
    
#     status = 'completed'
#     result = 'black' if user_id == match.white_id else 'black'

#     db_update_match(
#         match_id,
#         # fen=new_fen,
#         status=status,
#         result=result
#     )
    

# @router.post(
#     path="/match/{match_id}/offer-draw", 
# )
# async def match_offer_draw(
#     match_id: str,
#     player_identity: Identity = Depends(get_identity), 
# ):
#     # i have to send a notification to other player
#     match_id = str(match_id)
#     match = db_get_match(match_id)
#     """
#     select * from match where match_id = $1
#     """
#     if not match: 
#         raise HTTPException(404, "Match not found")
    
#     if player_identity.sub not in [match.white_id, match.black_id]:
#         raise HTTPException(403, "Player not eligible")
    
#     if match.status != 'active':
#         raise HTTPException(400, "Match not active")

# @router.post(
#     path="/match/{match_id}/accept-draw",
# )
# async def match_accept_draw(
#     match_id: str,
#     player_identity: Identity = Depends(get_identity), 
# ):
#     pass


# @router.post(
#     path="/match/{match_id}/claim-timeout",
# )
# async def match_claim_timeout(
#     match_id: str,
#     player_identity: Identity = Depends(get_identity), 
# ):
#     pass