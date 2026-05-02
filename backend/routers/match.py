from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket
from http import HTTPStatus
from pydantic import ValidationError
import uuid
import chess
import chess.engine
from datetime import datetime, timezone
from utils import get_user_id, calculate_elos, ConnectionManager, get_user_id_from_token
from models.game import TimeControlModel
from models.match import MatchModel, MatchStateModel
from models.account import EngineConfigModel
from schemas.match.requests import MatchMoveRequest
from schemas.match.responses import MatchMoveResponse, MatchFetchResponse, MoveEntry
from db.queries import (
    get_match_by_id, get_match_state_by_id, get_time_control_by_id,
    call_handle_match_move, call_handle_timeout, get_engine_config_from_account_id
)

router = APIRouter(
    prefix="/match",
    tags=["match"]
)

manager = ConnectionManager()

# NOTE: to override usual get_user_id from utils
# def get_user_id():
#     return uuid.UUID("a1000000-0000-0000-0000-000000000001")


############# for clear seperation of exceptions

class MatchNotFound(Exception):        pass
class MatchStateNotFound(Exception):   pass
class TimeControlNotFound(Exception):  pass
class DataIntegrityError(Exception):   pass
class NotAPlayer(Exception):           pass
class MatchNotActive(Exception):       pass
class NotYourTurn(Exception):          pass
class InvalidMove(Exception):          pass


############ shared execute move function

async def execute_move(
    match_id:  uuid.UUID,
    user_id:   uuid.UUID,
    uci:       str,
    played_at: datetime,
) -> tuple[MatchMoveResponse, chess.Board, MatchModel]:
    """
    Core move logic shared by the HTTP endpoint and the engine background task.
    Raises typed exceptions — callers map these to HTTP status codes or logs.
    """

    # fetch match record and check its existence
    match_record = await get_match_by_id(match_id)
    if not match_record:
        raise MatchNotFound("`match` record not found")

    # validate match record against MatchModel (db model)
    try:
        match = MatchModel.model_validate(dict(match_record))
    except ValidationError as e:
        raise DataIntegrityError(f"`match` record corrupted: {e}")

    # check the moves are only done by players of a match
    is_white = match.white_id is not None and user_id == match.white_id
    is_black = match.black_id is not None and user_id == match.black_id
    if not (is_white or is_black):
        raise NotAPlayer("You are not a player in this match")

    # check if moves are only made on an active match
    if match.status != 'active':
        raise MatchNotActive("Match is not active")

    # fetch time_control record and check its existence
    time_control_record = await get_time_control_by_id(match.time_control_id)
    if not time_control_record:
        raise TimeControlNotFound("`time_control` record not found")

    # validate time_control record against TimeControlModel (db model)
    try:
        time_control = TimeControlModel.model_validate(dict(time_control_record))
    except ValidationError as e:
        raise DataIntegrityError(f"`time_control` record corrupted: {e}")

    # fetch corresponding match state record
    match_state_record = await get_match_state_by_id(match_id)
    if not match_state_record:
        raise MatchStateNotFound("`match_state` record not found - trigger error")

    # validate match state against MatchStateModel (db model)
    try:
        match_state = MatchStateModel.model_validate(dict(match_state_record))
    except ValidationError as e:
        raise DataIntegrityError(f"`match_state` record corrupted: {e}")

    # load fen into board and check if fen is valid
    try:
        board = chess.Board(match_state.fen)
        if not board.is_valid():
            raise DataIntegrityError("Corrupt FEN")
    except DataIntegrityError:
        raise
    except Exception as e:
        raise DataIntegrityError(f"Invalid FEN: {e}")

    # check if it is the player's turn or not
    player_color   = 'white' if is_white else 'black'
    opponent_color = 'black' if is_white else 'white'
    if board.turn != (player_color == 'white'):
        raise NotYourTurn("Not your turn")

    # validate the move passed and check if it is legal or not
    try:
        move = chess.Move.from_uci(uci)
    except chess.InvalidMoveError:
        raise InvalidMove("Invalid UCI move format")
    if move not in board.legal_moves:
        raise InvalidMove("Illegal move")
    san_move = board.san(move)

    # calculate elapsed time based on the time when move is played at
    elapsed_ms = max(0, int((played_at - match_state.turn_started_at).total_seconds() * 1000))

    # calculate remaining times using elapsed time and check timeout
    times = {
        "white": match_state.white_time_remaining_ms,
        "black": match_state.black_time_remaining_ms,
    }
    times[player_color] -= elapsed_ms
    istimeout = times[player_color] < 0

    # check consequences of status, result, ended_at on making a move
    status, result, ended_at = 'active', None, None

    if istimeout:
        # NOTE: on timeout no move shd be pushed
        times[player_color] = 0  # clamp to zero
        status, ended_at = 'completed', played_at
        opp_color_const = chess.BLACK if is_white else chess.WHITE
        result = "draw" if board.has_insufficient_material(opp_color_const) else opponent_color
    else:
        # NOTE: when no timeout then push move and do incr
        times[player_color] += time_control.incr_time * 1000
        board.push(move)
        outcome = board.outcome(claim_draw=False)
        if outcome:
            status, ended_at = 'completed', played_at
            if outcome.winner == chess.WHITE:
                result = "white"
            elif outcome.winner == chess.BLACK:
                result = "black"
            else:
                result = "draw"

    # calculate elo changes based on effects on status
    if status == 'completed':
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
        #     times["white"],
        #     times["black"],
        #     elapsed_ms,
        #     result,
        #     ended_at,
        #     white_elo_shift,
        #     black_elo_shift
        # )
        pass
    else:
        await call_handle_match_move(
            match_id,
            match_state.move_number + 1,
            uci,
            board.fen(),
            times["white"],
            times["black"],
            status,
            played_at,
            result,
            ended_at,
            white_elo_shift,
            black_elo_shift,
        )

    response = MatchMoveResponse(
        fen=board.fen() if not istimeout else match_state.fen,
        status=status,
        result=result,
        uci=uci if not istimeout else None,
        san=san_move if not istimeout else None,
        server_now=played_at,
        turn_started_at=played_at,
        white_time_remaining_ms=times["white"],
        black_time_remaining_ms=times["black"],
    )

    return response, board, match


############# for background task

async def handle_engine_move_task(
    match_id:   uuid.UUID,
    bot_id:     uuid.UUID,
    fen:        str,
    engine_cfg: EngineConfigModel,
):
    print(f"[engine] task started for match {match_id}")
    try:
        print(f"[engine] opening stockfish...")
        transport, engine = await chess.engine.popen_uci("/usr/bin/stockfish")
        try:
            board = chess.Board(fen)
            print(f"[engine] playing move at depth {engine_cfg.depth}...")
            play_result = await engine.play(board, chess.engine.Limit(depth=engine_cfg.depth))
            bot_uci = play_result.move.uci()
            print(f"[engine] stockfish played: {bot_uci}")
        finally:
            await engine.quit()

        played_at = datetime.now(timezone.utc)
        print(f"[engine] calling execute_move...")
        response, _, _ = await execute_move(match_id, bot_id, bot_uci, played_at)
        print(f"[engine] execute_move done, broadcasting...")

        await manager.broadcast_to_match(str(match_id), {
            "type": "MOVE_MADE",
            "payload": response.model_dump(mode='json'),
        })
        print(f"[engine] broadcast done")

    except Exception as e:
        print(f"[engine] FAILED: {type(e).__name__}: {e}")
        await manager.broadcast_to_match(str(match_id), {
            "type": "ENGINE_ERROR",
            "payload": {"detail": str(e)},
        })


############ ENDPOINTS

# NOTE: timeout logic still to be implemented and what i expose shd also be checked
@router.get(
    path="/{match_id}",
    response_model=MatchFetchResponse
)
async def match_fetch_info(
    match_id: uuid.UUID     # path param
):
    """
    Anyone should be able to fetch the state of a match given the corresponding id.
    Unlike making moves which is restricted to players.
    Spectators of a match need not be restricted to just the players and can see completed and active matches.
    """
    fetch_now = datetime.now(timezone.utc)

    # fetch match record and check its existence
    match_record = await get_match_by_id(match_id)
    if not match_record:
        raise HTTPException(HTTPStatus.NOT_FOUND, "`match` record not found")

    # validate match record against MatchModel (db model)
    try:
        match = MatchModel.model_validate(dict(match_record))
    except ValidationError as e:
        raise HTTPException(HTTPStatus.INTERNAL_SERVER_ERROR, f"Data integrity error: `match` record corrupted {e}")

    # fetch corresponding match state record
    match_state_record = await get_match_state_by_id(match_id)
    if not match_state_record:
        raise HTTPException(HTTPStatus.INTERNAL_SERVER_ERROR, "`match_state` record not found - trigger error")

    # validate match state against MatchStateModel (db model)
    try:
        match_state = MatchStateModel.model_validate(dict(match_state_record))
    except ValidationError as e:
        raise HTTPException(HTTPStatus.INTERNAL_SERVER_ERROR, f"Data integrity error: `match_state` record corrupted {e}")

    # reconstruct uci and san moves from move_history (TEXT[] of UCI strings)
    moves: list[MoveEntry] = []
    if match_state.move_history:
        board = chess.Board()
        for uci_str in match_state.move_history:
            try:
                move = chess.Move.from_uci(uci_str)
                san  = board.san(move)
                board.push(move)
                moves.append(MoveEntry(uci=uci_str, san=san))
            except Exception as e:
                raise HTTPException(HTTPStatus.INTERNAL_SERVER_ERROR, f"Data integrity error: `move_history` has invalid uci moves {e}")

    # adjust clocks for time elapsed since turn started
    player_color = "white" if chess.Board(match_state.fen).turn == chess.WHITE else "black"
    times = {
        "white": match_state.white_time_remaining_ms,
        "black": match_state.black_time_remaining_ms,
    }

    if match.status == "active":
        elapsed_ms = max(0, int((fetch_now - match_state.turn_started_at).total_seconds() * 1000))
        times[player_color] -= elapsed_ms
        if times[player_color] < 0:
            # NOTE: enforce a handle_timeout function here
            pass

    return MatchFetchResponse(
        match_id=match_id,
        white_elo_initial=match.white_elo_initial,
        black_elo_initial=match.black_elo_initial,
        started_at=match.started_at,
        status=match.status,
        result=match.result,
        ended_at=match.ended_at,
        fen=match_state.fen,
        white_time_remaining_ms=times["white"],
        black_time_remaining_ms=times["black"],
        turn_started_at=match_state.turn_started_at,
        move_number=match_state.move_number,
        moves=moves,
    )


@router.websocket("/ws/{match_id}")
async def match_websocket(
    websocket: WebSocket,
    match_id:  uuid.UUID,
    token:     str,
):
    try:
        user_id = get_user_id_from_token(token)
    except HTTPException:
        await websocket.close(code=4001)
        return

    match_id_str = str(match_id)
    await manager.connect(websocket, match_id_str)
    try:
        while True:
            await websocket.receive_text()  # keep-alive / future: resign, draw signals
    except Exception:
        pass
    finally:
        manager.disconnect(websocket, match_id_str)


@router.post(
    path="/{match_id}/move",
    response_model=MatchMoveResponse
)
async def match_make_move(
    match_id:         uuid.UUID,
    request:          MatchMoveRequest,
    background_tasks: BackgroundTasks,
    user_id:          uuid.UUID = Depends(get_user_id),
):
    played_at = datetime.now(timezone.utc)

    try:
        response, board, match = await execute_move(match_id, user_id, request.uci, played_at)
    except (MatchNotFound, TimeControlNotFound) as e:
        raise HTTPException(HTTPStatus.NOT_FOUND, str(e))
    except (MatchStateNotFound, DataIntegrityError) as e:
        raise HTTPException(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))
    except NotAPlayer as e:
        raise HTTPException(HTTPStatus.FORBIDDEN, str(e))
    except (MatchNotActive, NotYourTurn, InvalidMove) as e:
        raise HTTPException(HTTPStatus.BAD_REQUEST, str(e))

    if response.status == 'active':
        next_player_id = match.white_id if board.turn == chess.WHITE else match.black_id
        engine_record = await get_engine_config_from_account_id(next_player_id)
        if engine_record:
            try:
                engine_cfg = EngineConfigModel.model_validate(dict(engine_record))
            except ValidationError as e:
                raise HTTPException(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    f"Data integrity error: `engine_account` record corrupted: {e}"
                )
            
            background_tasks.add_task(
                handle_engine_move_task,
                match_id,
                next_player_id,
                board.fen(),
                engine_cfg,
            )

    # return enough info for frontend clock sync
    return response


# @router.post(
#     path="/{match_id}/resign"
# )
# async def match_resign(
#     match_id: uuid.UUID,
#     user_id: uuid.UUID = Depends(get_user_id),
# ):
#     match_record = await get_match_by_id(match_id)
#     if not match_record:
#         raise HTTPException(HTTPStatus.NOT_FOUND, "Match not found")
#     match = MatchModel.model_validate(dict(match_record))
#     if user_id not in (match.white_id, match.black_id):
#         raise HTTPException(HTTPStatus.FORBIDDEN, "Player not eligible")
#     if match.status != 'active':
#         raise HTTPException(HTTPStatus.BAD_REQUEST, "Match not active")
#     status = 'completed'
#     result = 'black' if user_id == match.white_id else 'white'
#     # await call_handle_resign(match_id, status, result)


# @router.post(
#     path="/{match_id}/offer-draw",
# )
# async def match_offer_draw(
#     match_id: uuid.UUID,
#     user_id: uuid.UUID = Depends(get_user_id),
# ):
#     # i have to send a notification to the other player
#     pass


# @router.post(
#     path="/{match_id}/accept-draw",
# )
# async def match_accept_draw(
#     match_id: uuid.UUID,
#     user_id: uuid.UUID = Depends(get_user_id),
# ):
#     pass


# @router.post(
#     path="/{match_id}/claim-timeout",
# )
# async def match_claim_timeout(
#     match_id: uuid.UUID,
#     user_id: uuid.UUID = Depends(get_user_id),
# ):
#     pass