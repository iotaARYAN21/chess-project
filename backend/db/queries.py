"""
queries.py
All database query functions for the chess application.
Every function acquires its own connection from the pool and releases it
automatically, so callers never have to manage connections.
"""

import uuid
from datetime import datetime
from typing import Optional
from .database import get_pool
import asyncpg


# ===========================================================================
# ACCOUNT
# ===========================================================================

async def get_account_by_username(username: str) -> Optional[asyncpg.Record]:
    """Fetch a single ACCOUNT row by username."""
    async with get_pool().acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM account WHERE username = $1", username
        )


async def get_account_by_id(account_id: uuid.UUID) -> Optional[asyncpg.Record]:
    """Fetch a single ACCOUNT row by its UUID."""
    async with get_pool().acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM account WHERE id = $1", account_id
        )


async def deactivate_account(account_id: uuid.UUID) -> None:
    """Soft-delete: set is_active = FALSE."""
    async with get_pool().acquire() as conn:
        await conn.execute(
            "UPDATE account SET is_active = FALSE WHERE id = $1", account_id
        )


# ===========================================================================
# PLAYER ACCOUNT  (human users)
# ===========================================================================

async def create_player_account(
    username: str,
    email: str,
    password_hash: str,
) -> uuid.UUID:
    """
    Insert into account → playable_account → player_account atomically.
    Returns the new player UUID.
    """
    async with get_pool().acquire() as conn:
        async with conn.transaction():
            new_id: uuid.UUID = await conn.fetchval(
                """
                INSERT INTO account (player_type, username)
                VALUES ('playable', $1)
                RETURNING id
                """,
                username,
            )
            await conn.execute(
                "INSERT INTO playable_account (id) VALUES ($1)", new_id
            )
            await conn.execute(
                """
                INSERT INTO player_account (id, email, password_hash)
                VALUES ($1, $2, $3)
                """,
                new_id, email, password_hash,
            )
            # Seed empty profile, stats rows, and session log
            await conn.execute(
                "INSERT INTO user_profile (id) VALUES ($1)", new_id
            )
            await conn.execute(
                """
                INSERT INTO user_session_log (id, n_quits_today)
                VALUES ($1, 0)
                """,
                new_id,
            )
        return new_id


async def get_player_by_email(email: str) -> Optional[asyncpg.Record]:
    """Look up a player by e-mail (used during login)."""
    async with get_pool().acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT a.id, a.username, a.is_active,
                   pa.email, pa.password_hash
            FROM   player_account pa
            JOIN   account        a  ON a.id = pa.id
            WHERE  pa.email = $1
            """,
            email,
        )


# ===========================================================================
# ENGINE ACCOUNT
# ===========================================================================

async def create_engine_account(
    username: str,
    version: str,
    depth: Optional[int] = None,
) -> uuid.UUID:
    """Insert into account → playable_account → engine_account."""
    async with get_pool().acquire() as conn:
        async with conn.transaction():
            new_id: uuid.UUID = await conn.fetchval(
                """
                INSERT INTO account (player_type, username)
                VALUES ('playable', $1)
                RETURNING id
                """,
                username,
            )
            await conn.execute(
                "INSERT INTO playable_account (id) VALUES ($1)", new_id
            )
            await conn.execute(
                """
                INSERT INTO engine_account (id, version, depth)
                VALUES ($1, $2, $3)
                """,
                new_id, version, depth,
            )
        return new_id


async def get_all_engines() -> list:
    """Return every engine account with its settings."""
    async with get_pool().acquire() as conn:
        return await conn.fetch(
            """
            SELECT a.id, a.username, a.is_active,
                   e.version, e.depth
            FROM   engine_account e
            JOIN   account        a ON a.id = e.id
            ORDER  BY a.username
            """
        )


# ===========================================================================
# USER PROFILE
# ===========================================================================

async def get_user_profile(username: str) -> Optional[asyncpg.Record]:
    """Return profile for a player including follower/friend counts."""
    async with get_pool().acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT a.username, up.bio, up.avatar_url,
                   up.n_followers, up.n_friends
            FROM   user_profile up
            JOIN   account      a ON a.id = up.id
            WHERE  a.username = $1
            """,
            username,
        )


async def update_user_profile(
    username: str,
    bio: Optional[str] = None,
    avatar_url: Optional[str] = None,
) -> None:
    """Partial update of a user's profile (only non-None fields changed)."""
    async with get_pool().acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id FROM account WHERE username = $1", username
        )
        if not user:
            raise ValueError(f"User '{username}' not found")
        if bio is not None:
            await conn.execute(
                "UPDATE user_profile SET bio = $1 WHERE id = $2",
                bio, user["id"],
            )
        if avatar_url is not None:
            await conn.execute(
                "UPDATE user_profile SET avatar_url = $1 WHERE id = $2",
                avatar_url, user["id"],
            )


# ===========================================================================
# USER STATS  (per game-mode ELO + win/loss/draw counters)
# ===========================================================================

async def get_user_stats_by_mode(userid:uuid.UUID) -> list:  #TODO -> it should be userid
    """
    Calls the stored function GET_USER_STATS_BY_MODE.
    Returns a list of records: (game_mode, elo, n_wins, n_losses, n_draws).
    """
    async with get_pool().acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM get_user_stats_by_mode($1)", userid
        )


async def update_user_elo(
    user_id: uuid.UUID,
    game_mode_id: uuid.UUID,
    elo_shift: int,
) -> None:
    """Increment ELO and update win/loss/draw counters after a match."""
    async with get_pool().acquire() as conn:
        await conn.execute(
            """
            UPDATE user_stats
            SET    elo = elo + $3
            WHERE  user_id      = $1
              AND  game_mode_id = $2
            """,
            user_id, game_mode_id, elo_shift,
        )


async def record_match_outcome(
    user_id: uuid.UUID,
    game_mode_id: uuid.UUID,
    outcome: str,          # 'win' | 'loss' | 'draw'
    elo_shift: int,
) -> None:
    """Atomically update ELO and the correct counter."""
    col_map = {"win": "n_wins", "loss": "n_losses", "draw": "n_draws"}
    if outcome not in col_map:
        raise ValueError(f"outcome must be 'win', 'loss', or 'draw', got '{outcome}'")
    col = col_map[outcome]

    async with get_pool().acquire() as conn:
        await conn.execute(
            f"""
            UPDATE user_stats
            SET    elo  = elo + $3,
                   {col} = {col} + 1
            WHERE  user_id      = $1
              AND  game_mode_id = $2
            """,
            user_id, game_mode_id, elo_shift,
        )


# ===========================================================================
# GAME MODE
# ===========================================================================

async def get_all_game_modes() -> list:
    async with get_pool().acquire() as conn:
        return await conn.fetch(
            "SELECT id, name, description FROM game_mode ORDER BY name"
        )


async def get_game_mode_by_name(name: str) -> Optional[asyncpg.Record]:
    async with get_pool().acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM game_mode WHERE name = $1", name
        )


# ===========================================================================
# TIME CONTROL
# ===========================================================================

async def get_time_controls_by_mode(game_mode_name: str) -> list:
    """All time controls that belong to a given game mode."""
    async with get_pool().acquire() as conn:
        return await conn.fetch(
            """
            SELECT tc.id, tc.base_time, tc.incr_time
            FROM   time_control tc
            JOIN   game_mode    gm ON gm.id = tc.game_mode_id
            WHERE  gm.name = $1
            ORDER  BY tc.base_time
            """,
            game_mode_name,
        )


async def get_time_control_by_id(tc_id: uuid.UUID) -> Optional[asyncpg.Record]:
    async with get_pool().acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM time_control WHERE id = $1", tc_id
        )


# ===========================================================================
# MATCH
# ===========================================================================

async def create_match(
    white_id: uuid.UUID,
    black_id: uuid.UUID,
    time_control_id: uuid.UUID,
    white_elo: int,
    black_elo: int,
) -> uuid.UUID:
    """Insert a new match in 'waiting' status and return its UUID."""
    tc = await get_time_control_by_id(time_control_id)
    if not tc:
        raise ValueError(f"Time control {time_control_id} not found")
    base_ms = tc["base_time"] * 1000

    async with get_pool().acquire() as conn:
        return await conn.fetchval(
            """
            INSERT INTO match
                (white_id, black_id, time_control_id, white_elo, black_elo,
                 white_time_remaining_ms, black_time_remaining_ms)
            VALUES ($1, $2, $3, $4, $5, $6, $6)
            RETURNING id
            """,
            white_id, black_id, time_control_id,
            white_elo, black_elo, base_ms,
        )


async def get_match_by_id(match_id: uuid.UUID) -> Optional[asyncpg.Record]:
    async with get_pool().acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM match WHERE id = $1", match_id
        )


async def get_active_matches() -> list:
    async with get_pool().acquire() as conn:
        return await conn.fetch(
            """
            SELECT m.*, wa.username AS white_username,
                         ba.username AS black_username
            FROM   match   m
            JOIN   account wa ON wa.id = m.white_id
            JOIN   account ba ON ba.id = m.black_id
            WHERE  m.status = 'active'
            ORDER  BY m.started_at DESC
            """
        )


async def start_match(match_id: uuid.UUID) -> None:
    async with get_pool().acquire() as conn:
        await conn.execute(
            """
            UPDATE match
            SET    status     = 'active',
                   started_at = NOW()
            WHERE  id         = $1
              AND  status     = 'waiting'
            """,
            match_id,
        )


async def complete_match(
    match_id: uuid.UUID,
    result: str,  # 'white' | 'black' | 'draw'
) -> None:
    async with get_pool().acquire() as conn:
        await conn.execute(
            """
            UPDATE match
            SET    status   = 'completed',
                   result   = $2,
                   ended_at = NOW()
            WHERE  id       = $1
            """,
            match_id, result,
        )


async def update_match_clock(
    match_id: uuid.UUID,
    white_ms: int,
    black_ms: int,
    current_turn: str,
    fen: str,
    pgn: Optional[str] = None,
) -> None:
    """Update clock, turn, board position after each move."""
    async with get_pool().acquire() as conn:
        await conn.execute(
            """
            UPDATE match
            SET    white_time_remaining_ms = $2,
                   black_time_remaining_ms = $3,
                   current_turn            = $4,
                   fen                     = $5,
                   pgn                     = COALESCE($6, pgn)
            WHERE  id = $1
            """,
            match_id, white_ms, black_ms, current_turn, fen, pgn,
        )


async def get_matches_by_game_mode(username: str, game_mode_name: str) -> list:
    """
    Calls stored function GET_MATCHES_BY_GAME_MODE.
    Returns matches played by a user in the given game mode.
    """
    async with get_pool().acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM get_matches_by_game_mode($1, $2)",
            username, game_mode_name,
        )


# ===========================================================================
# MOVE
# ===========================================================================

async def record_move(
    match_id: uuid.UUID,
    move_number: int,
    player_color: str,
    uci: str,
    time_spent_ms: int,
) -> uuid.UUID:
    async with get_pool().acquire() as conn:
        return await conn.fetchval(
            """
            INSERT INTO move
                (match_id, move_number, player_color, uci, time_spent_ms)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            match_id, move_number, player_color, uci, time_spent_ms,
        )


async def get_moves_for_match(match_id: uuid.UUID) -> list:
    async with get_pool().acquire() as conn:
        return await conn.fetch(
            """
            SELECT move_number, player_color, uci,
                   time_spent_ms, played_at
            FROM   move
            WHERE  match_id = $1
            ORDER  BY move_number, player_color
            """,
            match_id,
        )


# ===========================================================================
# MATCH LOG  (ELO history)
# ===========================================================================

async def log_match_elo(
    match_id: uuid.UUID,
    player_id: uuid.UUID,
    elo_shift: int,
) -> None:
    async with get_pool().acquire() as conn:
        await conn.execute(
            """
            INSERT INTO match_log (match_id, player_id, elo_shift)
            VALUES ($1, $2, $3)
            """,
            match_id, player_id, elo_shift,
        )


async def get_elo_history(username: str, limit: int = 20) -> list:
    async with get_pool().acquire() as conn:
        return await conn.fetch(
            """
            SELECT ml.elo_shift, ml.log_time, m.result,
                   wa.username AS white, ba.username AS black
            FROM   match_log ml
            JOIN   account   a  ON a.id  = ml.player_id
            JOIN   match     m  ON m.id  = ml.match_id
            JOIN   account   wa ON wa.id = m.white_id
            JOIN   account   ba ON ba.id = m.black_id
            WHERE  a.username = $1
            ORDER  BY ml.log_time DESC
            LIMIT  $2
            """,
            username, limit,
        )


# ===========================================================================
# GAME SEEK
# ===========================================================================

async def create_game_seek(
    seeker_id: uuid.UUID,
    time_control_id: uuid.UUID,
    color_preference: str = "random",
) -> uuid.UUID:
    async with get_pool().acquire() as conn:
        return await conn.fetchval(
            """
            INSERT INTO game_seek
                (seeker_id, time_control_id, color_preference)
            VALUES ($1, $2, $3)
            RETURNING id
            """,
            seeker_id, time_control_id, color_preference,
        )


async def get_open_seeks(time_control_id: uuid.UUID) -> list:
    """Find all open (unmatched, unexpired) seeks for a given time control."""
    async with get_pool().acquire() as conn:
        return await conn.fetch(
            """
            SELECT gs.*, a.username
            FROM   game_seek gs
            JOIN   account   a ON a.id = gs.seeker_id
            WHERE  gs.time_control_id = $1
              AND  gs.status          = 'open'
              AND  gs.expires_at      > NOW()
            ORDER  BY gs.created_at ASC
            """,
            time_control_id,
        )


async def match_game_seek(seek_id: uuid.UUID, match_id: uuid.UUID) -> None:
    """Mark a seek as matched and link it to the resulting match."""
    async with get_pool().acquire() as conn:
        await conn.execute(
            """
            UPDATE game_seek
            SET    status  = 'matched',
                   game_id = $2
            WHERE  id      = $1
            """,
            seek_id, match_id,
        )


async def cancel_game_seek(seek_id: uuid.UUID) -> None:
    async with get_pool().acquire() as conn:
        await conn.execute(
            "UPDATE game_seek SET status = 'cancelled' WHERE id = $1",
            seek_id,
        )


async def expire_old_seeks() -> int:
    """Bulk-expire all seeks past their expires_at timestamp. Returns row count."""
    async with get_pool().acquire() as conn:
        result = await conn.execute(
            """
            UPDATE game_seek
            SET    status = 'expired'
            WHERE  status     = 'open'
              AND  expires_at <= NOW()
            """
        )
        return int(result.split()[-1])


# ===========================================================================
# FRIENDSHIP
# ===========================================================================

async def get_friends(username: str) -> list:
    async with get_pool().acquire() as conn:
        return await conn.fetch(
            """
            SELECT friend.username, up.bio, up.avatar_url, f.since
            FROM   account a
            JOIN   friendship f ON (f.user1_id = a.id OR f.user2_id = a.id)
            JOIN   account friend ON friend.id = CASE
                                       WHEN f.user1_id = a.id THEN f.user2_id
                                       ELSE f.user1_id
                                   END
            LEFT   JOIN user_profile up ON up.id = friend.id
            WHERE  a.username = $1
            ORDER  BY friend.username
            """,
            username,
        )


async def add_friendship(user1_id: uuid.UUID, user2_id: uuid.UUID) -> None:
    """Insert an ordered friendship row (user1 < user2)."""
    lo, hi = sorted([user1_id, user2_id])
    async with get_pool().acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "INSERT INTO friendship (user1_id, user2_id) VALUES ($1, $2)",
                lo, hi,
            )
            # Bump friend counters
            await conn.execute(
                "UPDATE user_profile SET n_friends = n_friends + 1 WHERE id IN ($1, $2)",
                user1_id, user2_id,
            )


async def remove_friendship(user1_id: uuid.UUID, user2_id: uuid.UUID) -> None:
    lo, hi = sorted([user1_id, user2_id])
    async with get_pool().acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "DELETE FROM friendship WHERE user1_id = $1 AND user2_id = $2",
                lo, hi,
            )
            await conn.execute(
                "UPDATE user_profile SET n_friends = GREATEST(n_friends - 1, 0) WHERE id IN ($1, $2)",
                user1_id, user2_id,
            )


# ===========================================================================
# FRIEND REQUEST
# ===========================================================================

async def send_friend_request(from_id: uuid.UUID, to_id: uuid.UUID) -> uuid.UUID:
    async with get_pool().acquire() as conn:

        existing = await conn.fetchrow(
            """
            SELECT 1 FROM friend_request
            WHERE from_user = $1 AND to_user = $2 AND status = 'pending'
            """,
            from_id, to_id
        )

        if existing:
            raise ValueError("Request already sent")

        return await conn.fetchval(
            """
            INSERT INTO friend_request (from_user, to_user)
            VALUES ($1, $2)
            RETURNING id
            """,
            from_id, to_id,
        )
    
async def get_friend_request_by_id(request_id: uuid.UUID,) -> Optional[asyncpg.Record]:
    """
    Fetch a friend request by its UUID.
    Includes both user IDs and usernames for downstream use.
    """
    async with get_pool().acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT fr.id,
                   fr.from_user,
                   fr.to_user,
                   fr.status,
                   a_from.username AS from_username,
                   a_to.username   AS to_username
            FROM   friend_request fr
            JOIN   account a_from ON a_from.id = fr.from_user
            JOIN   account a_to   ON a_to.id   = fr.to_user
            WHERE  fr.id = $1
            """,
            request_id,
        )

async def get_pending_friend_requests(username: str) -> list:
    async with get_pool().acquire() as conn:
        return await conn.fetch(
            """
            SELECT fr.id,
                   fr.status,
                   a_from.username AS from_username
            FROM friend_request fr
            JOIN account a_to   ON a_to.id = fr.to_user
            JOIN account a_from ON a_from.id = fr.from_user
            WHERE a_to.username = $1
              AND fr.status = 'pending'
            ORDER BY fr.id DESC
            """,
            username,
        )


async def respond_to_friend_request(
    request_id: uuid.UUID,
    status: str,  # 'accepted' | 'declined' | 'cancelled'
) -> None:
    if status not in ("accepted", "declined", "cancelled"):
        raise ValueError(f"Invalid status '{status}'")
    async with get_pool().acquire() as conn:
        await conn.execute(
            "UPDATE friend_request SET status = $2 WHERE id = $1",
            request_id, status,
        )


# ===========================================================================
# FOLLOWER
# ===========================================================================

async def follow_user(follower_id: uuid.UUID, followed_id: uuid.UUID) -> None:
    async with get_pool().acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "INSERT INTO follower (follower_id, followed_id) VALUES ($1, $2)",
                follower_id, followed_id,
            )
            await conn.execute(
                "UPDATE user_profile SET n_followers = n_followers + 1 WHERE id = $1",
                followed_id,
            )


async def unfollow_user(follower_id: uuid.UUID, followed_id: uuid.UUID) -> None:
    async with get_pool().acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "DELETE FROM follower WHERE follower_id = $1 AND followed_id = $2",
                follower_id, followed_id,
            )
            await conn.execute(
                "UPDATE user_profile SET n_followers = GREATEST(n_followers - 1, 0) WHERE id = $1",
                followed_id,
            )


async def get_followers(username: str) -> list:
    async with get_pool().acquire() as conn:
        return await conn.fetch(
            """
            SELECT a.username, up.avatar_url, f.since
            FROM   follower      f
            JOIN   account       followed ON followed.username = $1
            JOIN   account       a        ON a.id = f.follower_id
            LEFT   JOIN user_profile up   ON up.id = a.id
            WHERE  f.followed_id = followed.id
            ORDER  BY f.since DESC
            """,
            username,
        )


# ===========================================================================
# USER SESSION LOG
# ===========================================================================

async def update_session_on_quit(user_id: uuid.UUID, match_id: uuid.UUID) -> None:
    """Increment quit counter and record the timestamp."""
    async with get_pool().acquire() as conn:
        await conn.execute(
            """
            UPDATE user_session_log
            SET    last_game_id  = $2,
                   last_quit_at  = NOW(),
                   n_quits_today = n_quits_today + 1
            WHERE  id = $1
            """,
            user_id, match_id,
        )


async def reset_daily_quit_counters() -> int:
    """Reset all n_quits_today to 0 (run via a nightly cron / scheduler)."""
    async with get_pool().acquire() as conn:
        result = await conn.execute(
            "UPDATE user_session_log SET n_quits_today = 0"
        )
        return int(result.split()[-1])


async def get_session_log(user_id: uuid.UUID) -> Optional[asyncpg.Record]:
    async with get_pool().acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM user_session_log WHERE id = $1", user_id
        )


# ===========================================================================
# BAN
# ===========================================================================

async def ban_user(
    account_id: uuid.UUID,
    admin_id: uuid.UUID,
    ban_type: str,
    reason: Optional[str],
    expires_at: Optional[datetime] = None,
) -> uuid.UUID:
    async with get_pool().acquire() as conn:
        return await conn.fetchval(
            """
            INSERT INTO ban
                (account_id, banned_by, ban_type, reason, expires_at)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            account_id, admin_id, ban_type, reason, expires_at,
        )


async def get_active_bans(account_id: uuid.UUID) -> list:
    """Return bans that are still in effect (permanent or not yet expired)."""
    async with get_pool().acquire() as conn:
        return await conn.fetch(
            """
            SELECT *
            FROM   ban
            WHERE  account_id = $1
              AND (ban_type  = 'permanent'
                   OR expires_at > NOW())
            ORDER  BY created_at DESC
            """,
            account_id,
        )


async def is_banned(account_id: uuid.UUID) -> bool:
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT 1 FROM ban
            WHERE  account_id = $1
              AND (ban_type  = 'permanent' OR expires_at > NOW())
            LIMIT 1
            """,
            account_id,
        )
        return row is not None


# ===========================================================================
# ANTI-CHEAT LOG
# ===========================================================================

async def log_suspicious_activity(
    user_id: uuid.UUID,
    match_id: uuid.UUID,
    sus_score: float,
) -> uuid.UUID:
    async with get_pool().acquire() as conn:
        return await conn.fetchval(
            """
            INSERT INTO anti_cheat_log (user_id, match_id, sus_score)
            VALUES ($1, $2, $3)
            RETURNING id
            """,
            user_id, match_id, sus_score,
        )


async def get_unresolved_cheat_logs() -> list:
    async with get_pool().acquire() as conn:
        return await conn.fetch(
            """
            SELECT acl.id, a.username, acl.match_id,
                   acl.sus_score, acl.added_at
            FROM   anti_cheat_log acl
            JOIN   account        a ON a.id = acl.user_id
            WHERE  acl.resolved = FALSE
            ORDER  BY acl.sus_score DESC
            """
        )


async def resolve_cheat_log(
    log_id: uuid.UUID,
    admin_id: uuid.UUID,
) -> None:
    async with get_pool().acquire() as conn:
        await conn.execute(
            """
            UPDATE anti_cheat_log
            SET    resolved    = TRUE,
                   resolved_by = $2,
                   resolved_at = NOW()
            WHERE  id          = $1
            """,
            log_id, admin_id,
        )


# ---------------------------------------------------------------------------
# Required at the top but placed here to avoid circular-import confusion
# when this file is read before asyncpg is installed.
# ---------------------------------------------------------------------------
try:
    import asyncpg
except ImportError:
    pass  # type: ignore