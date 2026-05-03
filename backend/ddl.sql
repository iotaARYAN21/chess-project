CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- NOTICE: NEW TABLE CREATED DUE TO ENGINE AND PLAYER SEPARATION
-- FUTURE WORK: REGEX MIGHT BE ADDED 
CREATE TABLE IF NOT EXISTS ACCOUNT (
    ID UUID PRIMARY KEY DEFAULT GEN_RANDOM_UUID(),
    PLAYER_TYPE VARCHAR(15) NOT NULL,
    USERNAME VARCHAR(30) NOT NULL UNIQUE,
    CREATED_AT TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    IS_ACTIVE BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT CHK_USERNAME_LENGTH CHECK (CHAR_LENGTH(USERNAME) >= 3),
    CONSTRAINT CHK_PLAYER_TYPE CHECK (PLAYER_TYPE IN ('playable', 'non_playable'))
);

-- PLAYABLE Branch
CREATE TABLE IF NOT EXISTS PLAYABLE_ACCOUNT (
    ID UUID PRIMARY KEY REFERENCES ACCOUNT (ID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS PLAYER_ACCOUNT (
    ID UUID PRIMARY KEY REFERENCES PLAYABLE_ACCOUNT (ID) ON DELETE CASCADE,
    EMAIL VARCHAR(255) NOT NULL UNIQUE,
    PASSWORD_HASH TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ENGINE_ACCOUNT (
    ID UUID PRIMARY KEY REFERENCES PLAYABLE_ACCOUNT (ID) ON DELETE CASCADE,
    VERSION VARCHAR(20) NOT NULL,
    DEPTH SMALLINT
);

-- NON_PLAYABLE Branch
-- CREATE TABLE IF NOT EXISTS NON_PLAYABLE_ACCOUNT (
--     ID UUID PRIMARY KEY REFERENCES ACCOUNT (ID) ON DELETE CASCADE
-- );

CREATE TABLE IF NOT EXISTS ADMIN_ACCOUNT (
    ID UUID PRIMARY KEY REFERENCES ACCOUNT (ID) ON DELETE CASCADE,
    ADMIN_LEVEL VARCHAR(20) NOT NULL DEFAULT 'moderator',
	EMAIL VARCHAR(255) NOT NULL UNIQUE,
    PASSWORD_HASH TEXT NOT NULL,
    CONSTRAINT CHK_ADMIN_LEVEL CHECK (ADMIN_LEVEL IN ('moderator', 'admin', 'super_admin'))
);

-- GAME MODE: bullet,blitz,rapid,classical 
CREATE TABLE IF NOT EXISTS GAME_MODE (
	ID UUID PRIMARY KEY DEFAULT GEN_RANDOM_UUID(),
	NAME VARCHAR(10) NOT NULL UNIQUE,
	DESCRIPTION VARCHAR(30) NOT NULL
);

-- TIME_CONTROL: 5+0,3+2,1+0,90+60
-- NOTICE: CHANGED GAME_TABLE -> TIME_CONTROL
-- NOTE SMALLINT holds: -32768 to 32767 seconds => 32767 / 60 = 546 minutes = 9.1 hours (Enough) 
CREATE TABLE IF NOT EXISTS TIME_CONTROL (
	ID UUID PRIMARY KEY DEFAULT GEN_RANDOM_UUID(),
	-- GAME_MODE_ID UUID REFERENCES GAME_MODE (ID),
	GAME_MODE_ID UUID NOT NULL REFERENCES GAME_MODE (ID),
	-- BASE_TIME SMALLINT NOT NULL, -- in seconds
	BASE_TIME INT NOT NULL, -- in seconds (as want long active matches)
	INCR_TIME SMALLINT NOT NULL DEFAULT 0, -- in seconds
	CONSTRAINT CHK_BASE_TIME CHECK (BASE_TIME > 0),
	CONSTRAINT CHK_INCR_TIME CHECK (INCR_TIME >= 0)
);

-- CREATE TABLE IF NOT EXISTS MATCH (
-- 	ID UUID PRIMARY KEY DEFAULT GEN_RANDOM_UUID(),
--     WHITE_ID UUID REFERENCES PLAYABLE_ACCOUNT (ID) ON DELETE SET NULL,
--     BLACK_ID UUID REFERENCES PLAYABLE_ACCOUNT (ID) ON DELETE SET NULL,
-- 	TIME_CONTROL_ID UUID NOT NULL REFERENCES TIME_CONTROL (ID),
-- 	-- STATUS VARCHAR(20) NOT NULL DEFAULT 'waiting', -- unclean if kept keep matchmaking seperate
-- 	STATUS VARCHAR(20) NOT NULL, -- (update ONCE END)
-- 	RESULT VARCHAR(10), -- this is already in pgn (redundant but keep it) (update ONCE END)
-- 	-- CURRENT_TURN VARCHAR(5) NOT NULL DEFAULT 'white', -- dont make default white (redundant) (FREQ UPDATES) not needed can take from fen
-- 	WHITE_TIME_REMAINING_MS INT NOT NULL, -- (FREQ UPDATES)
-- 	BLACK_TIME_REMAINING_MS INT NOT NULL, -- (FREQ UPDATES)
-- 	-- WHITE_TIMESTAMP INT NOT NULL, -- for computing delta (FREQ UPDATES) not needed
-- 	-- BLACK_TIMESTAMP INT NOT NULL, -- for computing delta (FREQ UPDATES) not needed
-- 	WHITE_ELO INT NOT NULL, -- white current elo before a match ends (update ONCE END)
-- 	BLACK_ELO INT NOT NULL, -- black current elo before match ends (update ONCE END)
-- 	MOVE_NUMBER SMALLINT NOT NULL,
-- 	PGN TEXT, -- move history before a move (FREQ UPDATES)
-- 	FEN TEXT NOT NULL DEFAULT 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', -- current turn already encoded (FREQ UPDATES)
-- 	-- STARTED_AT TIMESTAMPTZ,
-- 	STARTED_AT TIMESTAMPTZ NOT NULL, -- no seeking so it has to be not null
-- 	ENDED_AT TIMESTAMPTZ, -- (update ONCE END)
-- 	CONSTRAINT CHECK_WHITE_BLACK CHECK (WHITE_ID <> BLACK_ID),
-- 	-- CONSTRAINT CHK_STATUS CHECK (STATUS IN ('waiting', 'active', 'completed')),
-- 	CONSTRAINT CHK_STATUS CHECK (STATUS IN ('active', 'completed')),
-- 	CONSTRAINT CHK_RESULT CHECK (
-- 		RESULT IS NULL
-- 		OR RESULT IN ('white', 'black', 'draw')
-- 	),
-- 	-- CONSTRAINT CHK_CURRENT_TURN CHECK (CURRENT_TURN IN ('white', 'black')),
-- 	CONSTRAINT CHK_RESULT_ON_COMPLETION CHECK (
-- 		(
-- 			STATUS = 'completed'
-- 			AND RESULT IS NOT NULL
-- 		)
-- 		OR (
-- 			STATUS <> 'completed'
-- 			AND RESULT IS NULL
-- 		)
-- 	),
-- 	CONSTRAINT CHK_WHITE_CLOCK CHECK (WHITE_TIME_REMAINING_MS >= 0),
-- 	CONSTRAINT CHK_BLACK_CLOCK CHECK (BLACK_TIME_REMAINING_MS >= 0),
-- 	CONSTRAINT CHK_END_AFTER_START CHECK (
-- 		ENDED_AT IS NULL
-- 		-- OR STARTED_AT IS NULL
-- 		OR ENDED_AT >= STARTED_AT
-- 	)
-- );


-- updated once only
CREATE TABLE IF NOT EXISTS MATCH (
    ID UUID PRIMARY KEY DEFAULT GEN_RANDOM_UUID(),
    WHITE_ID UUID REFERENCES PLAYABLE_ACCOUNT(ID) ON DELETE SET NULL,
    BLACK_ID UUID REFERENCES PLAYABLE_ACCOUNT(ID) ON DELETE SET NULL,
    TIME_CONTROL_ID UUID NOT NULL REFERENCES TIME_CONTROL(ID),
    
    -- Initial state
    WHITE_ELO_INITIAL INT NOT NULL CHECK (WHITE_ELO_INITIAL >= 0),
    BLACK_ELO_INITIAL INT NOT NULL CHECK (BLACK_ELO_INITIAL >= 0),
    STARTED_AT TIMESTAMPTZ NOT NULL,
    
    -- Final state (updated ONCE)
    STATUS VARCHAR(20) NOT NULL CHECK (STATUS IN ('active', 'completed')),
    RESULT VARCHAR(10) CHECK (RESULT IS NULL OR RESULT IN ('white', 'black', 'draw')),
	ENDED_AT TIMESTAMPTZ,
	WHITE_ELO_SHIFT INT,
	BLACK_ELO_SHIFT INT,
	FINAL_FEN TEXT,
	FINAL_PGN TEXT,
    
    CONSTRAINT CHECK_WHITE_BLACK CHECK (WHITE_ID IS NULL OR BLACK_ID IS NULL OR WHITE_ID <> BLACK_ID),
	CONSTRAINT CHK_END_AFTER_START CHECK (ENDED_AT IS NULL OR ENDED_AT >= STARTED_AT),
	CONSTRAINT CHK_MATCH_LIFECYCLE CHECK (
        (STATUS = 'active' AND 
         RESULT IS NULL AND 
         ENDED_AT IS NULL AND 
		 WHITE_ELO_SHIFT IS NULL AND
		 BLACK_ELO_SHIFT IS NULL AND
		 FINAL_FEN IS NULL AND 
         FINAL_PGN IS NULL)
        OR 
        (STATUS = 'completed' AND 
         RESULT IS NOT NULL AND 
         ENDED_AT IS NOT NULL AND 
		 WHITE_ELO_SHIFT IS NOT NULL AND
		 BLACK_ELO_SHIFT IS NOT NULL AND
		 FINAL_FEN IS NOT NULL AND 
         FINAL_PGN IS NOT NULL)
    )

);

-- frequently updated
-- lets just delete it after use 
-- easy to move to something like redis and keep seperation of hot and cold data
-- TODO: draw offered by still needs to be added
CREATE TABLE IF NOT EXISTS MATCH_STATE (
    MATCH_ID UUID PRIMARY KEY REFERENCES MATCH(ID) ON DELETE CASCADE,
    
	-- DRAW_OFFERED_BY UUID REFERENCES playable_account(id) ON DELETE SET NULL,
    FEN TEXT NOT NULL,
    
    WHITE_TIME_REMAINING_MS INT NOT NULL CHECK (WHITE_TIME_REMAINING_MS >= 0),
    BLACK_TIME_REMAINING_MS INT NOT NULL CHECK (BLACK_TIME_REMAINING_MS >= 0),
    TURN_STARTED_AT TIMESTAMPTZ NOT NULL,
    
    MOVE_NUMBER SMALLINT NOT NULL CHECK (MOVE_NUMBER >= 0),
	MOVE_HISTORY TEXT[] NOT NULL
);

-- add a trigger just for this is this even needed maybe only completed games
-- NOTE: this is for calculating the stats for player 
-- i can filter by player_id and get a graph from this
CREATE TABLE IF NOT EXISTS MATCH_LOG (
	ID UUID PRIMARY KEY DEFAULT GEN_RANDOM_UUID(),
	MATCH_ID UUID NOT NULL REFERENCES MATCH (ID) ON DELETE CASCADE,
	PLAYER_ID UUID REFERENCES PLAYABLE_ACCOUNT (ID) ON DELETE SET NULL,
	PLAYER_SIDE CHAR(1) NOT NULL CHECK (PLAYER_SIDE IN ('w', 'b')),
	ELO_BEFORE INT NOT NULL CHECK (ELO_BEFORE >= 0),
	ELO_SHIFT INT NOT NULL,
	ENDED_AT TIMESTAMPTZ NOT NULL,

	CONSTRAINT UQ_MATCH_PLAYER_LOG UNIQUE (MATCH_ID, PLAYER_SIDE)
);



-- Purpose: 
-- 1) When a user seeks a challenge, an instance of GAME_SEEK is created
-- 2) Two users who have issued a seek will be paired up with each other if certain conditions meet 
-- 3) The condition could be based on color preference or if time had exceed certain limit then 
-- certain conditions are neglected and players are paired up regardless.
CREATE TABLE IF NOT EXISTS GAME_SEEK (
	ID UUID PRIMARY KEY DEFAULT GEN_RANDOM_UUID(),
    SEEKER_ID UUID NOT NULL REFERENCES PLAYER_ACCOUNT (ID) ON DELETE CASCADE,
	TIME_CONTROL_ID UUID NOT NULL REFERENCES TIME_CONTROL (ID),
	COLOR_PREFERENCE VARCHAR(10) NOT NULL DEFAULT 'random',
	STATUS VARCHAR(10) NOT NULL DEFAULT 'open',
	CREATED_AT TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	EXPIRES_AT TIMESTAMPTZ NOT NULL DEFAULT NOW() + INTERVAL '10 minutes',
	GAME_ID UUID REFERENCES MATCH (ID), -- should be populated once matched
	CONSTRAINT CHK_SEEK_STATUS CHECK (
		STATUS IN ('open', 'matched', 'cancelled', 'expired')
	),
	CONSTRAINT CHK_COLOR_PREF CHECK (COLOR_PREFERENCE IN ('white', 'black', 'random')),
	CONSTRAINT CHK_SEEK_EXPIRES_AFTER_CREATED CHECK (EXPIRES_AT > CREATED_AT),
	CONSTRAINT CHK_GAME_ON_MATCH CHECK (
		(
			STATUS = 'matched'
			AND GAME_ID IS NOT NULL
		)
		OR (
			STATUS <> 'matched'
			AND GAME_ID IS NULL
		)
	)
);

-- Purpose: User profile
CREATE TABLE IF NOT EXISTS USER_PROFILE (
	ID UUID PRIMARY KEY REFERENCES PLAYER_ACCOUNT (ID) ON DELETE CASCADE,
	BIO TEXT,
	AVATAR_URL TEXT,
	N_FOLLOWERS INT NOT NULL DEFAULT 0,
	N_FRIENDS INT NOT NULL DEFAULT 0,
	CONSTRAINT CHK_N_FOLLOWERS CHECK (N_FOLLOWERS >= 0),
	CONSTRAINT CHK_N_FRIENDS CHECK (N_FRIENDS >= 0)
);

-- Purpose: per game mode statistics for human users
CREATE TABLE IF NOT EXISTS USER_STATS (
	USER_ID UUID NOT NULL REFERENCES PLAYER_ACCOUNT (ID) ON DELETE CASCADE,
	-- GAME_MODE_ID UUID NOT NULL REFERENCES GAME_MODE (ID) ON DELETE CASCADE,
	GAME_MODE_ID UUID NOT NULL REFERENCES GAME_MODE (ID),
	ELO SMALLINT NOT NULL DEFAULT 1200,
	N_WINS INT NOT NULL DEFAULT 0,
	N_LOSSES INT NOT NULL DEFAULT 0,
	N_DRAWS INT NOT NULL DEFAULT 0,
	PRIMARY KEY (USER_ID, GAME_MODE_ID),
	CONSTRAINT CHK_ELO CHECK (ELO >= 0),
	CONSTRAINT CHK_N_WINS CHECK (N_WINS >= 0),
	CONSTRAINT CHK_N_LOSSES CHECK (N_LOSSES >= 0),
	CONSTRAINT CHK_N_DRAWS CHECK (N_DRAWS >= 0)
);

-- Purpose:
-- 1) logs user last match played, number of quits for today
-- 2) Used to ban people for high number of quitting games
CREATE TABLE IF NOT EXISTS USER_SESSION_LOG (
	ID UUID PRIMARY KEY REFERENCES PLAYER_ACCOUNT (ID) ON DELETE CASCADE,
	LAST_GAME_ID UUID REFERENCES MATCH (ID) ON DELETE SET NULL,
	LAST_QUIT_AT TIMESTAMPTZ,
	N_QUITS_TODAY SMALLINT NOT NULL DEFAULT 0,
	CONSTRAINT CHK_N_QUITS CHECK (N_QUITS_TODAY >= 0)
);

CREATE TABLE IF NOT EXISTS FRIENDSHIP (
	USER1_ID UUID NOT NULL REFERENCES PLAYER_ACCOUNT (ID) ON DELETE CASCADE,
	USER2_ID UUID NOT NULL REFERENCES PLAYER_ACCOUNT (ID) ON DELETE CASCADE,
	SINCE TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	PRIMARY KEY (USER1_ID, USER2_ID),
	CONSTRAINT CHK_NOT_SELF_FRIEND CHECK (USER1_ID <> USER2_ID),
	-- to prevent (A,B) and (B,A) duplicates
	CONSTRAINT CHK_ORDERED_FRIENDSHIP CHECK (USER1_ID < USER2_ID)
);

CREATE TABLE IF NOT EXISTS FOLLOWER (
	FOLLOWER_ID UUID NOT NULL REFERENCES PLAYER_ACCOUNT (ID) ON DELETE CASCADE,
	FOLLOWED_ID UUID NOT NULL REFERENCES PLAYER_ACCOUNT (ID) ON DELETE CASCADE,
	SINCE TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	PRIMARY KEY (FOLLOWER_ID, FOLLOWED_ID),
	CONSTRAINT CHK_NOT_SELF_FOLLOW CHECK (FOLLOWER_ID <> FOLLOWED_ID)
);

CREATE TABLE IF NOT EXISTS FRIEND_REQUEST (
	ID UUID PRIMARY KEY DEFAULT GEN_RANDOM_UUID(),
	FROM_USER UUID NOT NULL REFERENCES PLAYER_ACCOUNT (ID) ON DELETE CASCADE,
	TO_USER UUID NOT NULL REFERENCES PLAYER_ACCOUNT (ID) ON DELETE CASCADE,
	STATUS VARCHAR(10) NOT NULL DEFAULT 'pending',
	CREATED_AT TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	CONSTRAINT CHK_NOT_SELF_REQUEST CHECK (FROM_USER <> TO_USER),
	CONSTRAINT CHK_FRIEND_REQUEST_STATUS CHECK (
		STATUS IN ('pending', 'accepted', 'declined', 'cancelled')
	)
);

CREATE TABLE IF NOT EXISTS BAN (
	ID UUID PRIMARY KEY DEFAULT GEN_RANDOM_UUID(),
	ACCOUNT_ID UUID NOT NULL REFERENCES PLAYER_ACCOUNT (ID) ON DELETE CASCADE,
	BANNED_BY UUID REFERENCES ADMIN_ACCOUNT (ID) ON DELETE SET NULL, -- admin who issued ban
	BAN_TYPE VARCHAR(20) NOT NULL,
	REASON TEXT,
	CREATED_AT TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	EXPIRES_AT TIMESTAMPTZ,
	CONSTRAINT CHK_BAN_TYPE CHECK (BAN_TYPE IN ('temporary', 'permanent')),
	CONSTRAINT CHK_EXPIRES_AFTER_CREATED CHECK (
		EXPIRES_AT IS NULL
		OR EXPIRES_AT > CREATED_AT
	),
	CONSTRAINT CHK_TEMP_BAN_HAS_EXPIRY CHECK (
		(
			BAN_TYPE = 'temporary'
			AND EXPIRES_AT IS NOT NULL
		)
		OR BAN_TYPE <> 'temporary'
	)
);

CREATE TABLE IF NOT EXISTS ANTI_CHEAT_LOG (
	ID UUID PRIMARY KEY DEFAULT GEN_RANDOM_UUID(),
	USER_ID UUID NOT NULL REFERENCES PLAYER_ACCOUNT (ID) ON DELETE CASCADE,
	MATCH_ID UUID NOT NULL REFERENCES MATCH (ID) ON DELETE CASCADE,
	SUS_SCORE NUMERIC(5, 2) NOT NULL,
	ADDED_AT TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	RESOLVED BOOLEAN NOT NULL DEFAULT FALSE,
	RESOLVED_BY UUID REFERENCES ADMIN_ACCOUNT (ID) ON DELETE SET NULL, -- admin account referened
	RESOLVED_AT TIMESTAMPTZ,
	CONSTRAINT CHK_SUS_SCORE CHECK (SUS_SCORE BETWEEN 0.00 AND 100.00),
	CONSTRAINT CHK_RESOLVED CHECK (
		(
			RESOLVED = TRUE
			AND RESOLVED_BY IS NOT NULL
			AND RESOLVED_AT IS NOT NULL
		)
		OR (
			RESOLVED = FALSE
			AND RESOLVED_BY IS NULL
			AND RESOLVED_AT IS NULL
		)
	)
);

-- INDEXES

-- Fast email-based login
CREATE UNIQUE INDEX IF NOT EXISTS idx_player_account_email
    ON PLAYER_ACCOUNT (EMAIL);

CREATE UNIQUE INDEX IF NOT EXISTS idx_admin_account_email
    ON ADMIN_ACCOUNT (EMAIL);

-- Username search / profile lookup
CREATE UNIQUE INDEX IF NOT EXISTS idx_account_username
    ON ACCOUNT (USERNAME);

-- Active-account filter (e.g. block deactivated users from login)
CREATE INDEX IF NOT EXISTS idx_account_is_active
    ON ACCOUNT (IS_ACTIVE);

-- "All games for player X" (history page) — one index per side
CREATE INDEX IF NOT EXISTS idx_match_white_id
    ON MATCH (WHITE_ID);

CREATE INDEX IF NOT EXISTS idx_match_black_id
    ON MATCH (BLACK_ID);

-- Lobby list (active) / archive (completed)
CREATE INDEX IF NOT EXISTS idx_match_status
    ON MATCH (STATUS);

-- Partial: only active games — tiny hot set, scanned constantly
CREATE INDEX IF NOT EXISTS idx_match_active
    ON MATCH (STARTED_AT DESC)
    WHERE STATUS = 'active';

-- Join MATCH → TIME_CONTROL (e.g. "all rapid games")
CREATE INDEX IF NOT EXISTS idx_match_time_control_id
    ON MATCH (TIME_CONTROL_ID);

-- Recent-games feed ordered by start time
CREATE INDEX IF NOT EXISTS idx_match_started_at
    ON MATCH (STARTED_AT DESC);

-- Composite: player + status — "active games for player X"
CREATE INDEX IF NOT EXISTS idx_match_white_status
    ON MATCH (WHITE_ID, STATUS);

CREATE INDEX IF NOT EXISTS idx_match_black_status
    ON MATCH (BLACK_ID, STATUS);

-- "All entries for player X ordered by time" (graph query)
CREATE INDEX IF NOT EXISTS idx_match_log_player_ended
    ON MATCH_LOG (PLAYER_ID, ENDED_AT ASC);

-- Join back to MATCH
CREATE INDEX IF NOT EXISTS idx_match_log_match_id
    ON MATCH_LOG (MATCH_ID);

-- Cross-mode profile lookup (PK already covers both cols together;
-- this standalone index covers WHERE USER_ID = ? alone)
CREATE INDEX IF NOT EXISTS idx_user_stats_user_id
    ON USER_STATS (USER_ID);

-- Leaderboard: top ELO per game mode
CREATE INDEX IF NOT EXISTS idx_user_stats_mode_elo
    ON USER_STATS (GAME_MODE_ID, ELO DESC);

-- Join: last game played by user
CREATE INDEX IF NOT EXISTS idx_session_log_last_game
    ON USER_SESSION_LOG (LAST_GAME_ID)
    WHERE LAST_GAME_ID IS NOT NULL;

-- Anti-quit enforcement: users who quit today
CREATE INDEX IF NOT EXISTS idx_session_log_quits
    ON USER_SESSION_LOG (N_QUITS_TODAY DESC)
    WHERE N_QUITS_TODAY > 0;

-- Matchmaking scan: open seeks for a given time-control
CREATE INDEX IF NOT EXISTS idx_game_seek_open_tc
    ON GAME_SEEK (TIME_CONTROL_ID, COLOR_PREFERENCE)
    WHERE STATUS = 'open';

-- Player's own seeks
CREATE INDEX IF NOT EXISTS idx_game_seek_seeker
    ON GAME_SEEK (SEEKER_ID, STATUS);

-- Expiry janitor job
CREATE INDEX IF NOT EXISTS idx_game_seek_expires_at
    ON GAME_SEEK (EXPIRES_AT)
    WHERE STATUS = 'open';


-- "Friends of X" — PK covers USER1_ID lookups;
-- need a separate index for the USER2_ID direction
CREATE INDEX IF NOT EXISTS idx_friendship_user2
    ON FRIENDSHIP (USER2_ID);


-- "Who follows X?" — PK covers FOLLOWER_ID; need FOLLOWED_ID
CREATE INDEX IF NOT EXISTS idx_follower_followed_id
    ON FOLLOWER (FOLLOWED_ID);

-- Inbox: pending requests TO a user
CREATE INDEX IF NOT EXISTS idx_friend_request_to_user
    ON FRIEND_REQUEST (TO_USER, STATUS);

-- Sent: requests FROM a user
CREATE INDEX IF NOT EXISTS idx_friend_request_from_user
    ON FRIEND_REQUEST (FROM_USER, STATUS);

-- "Is player X currently banned?" — checked on every login/move
CREATE INDEX IF NOT EXISTS idx_ban_account_id
    ON BAN (ACCOUNT_ID);

-- Partial: only bans that haven't expired yet (small active set)
CREATE INDEX IF NOT EXISTS idx_ban_active
    ON BAN (ACCOUNT_ID, EXPIRES_AT)
    WHERE EXPIRES_AT IS NULL;

-- Admin: bans issued by a specific moderator
CREATE INDEX IF NOT EXISTS idx_ban_banned_by
    ON BAN (BANNED_BY)
    WHERE BANNED_BY IS NOT NULL;

-- "All flags for player X"
CREATE INDEX IF NOT EXISTS idx_anti_cheat_user_id
    ON ANTI_CHEAT_LOG (USER_ID);

-- "All flags for match Y"
CREATE INDEX IF NOT EXISTS idx_anti_cheat_match_id
    ON ANTI_CHEAT_LOG (MATCH_ID);

-- Admin review queue: unresolved flags by suspicion score
CREATE INDEX IF NOT EXISTS idx_anti_cheat_unresolved
    ON ANTI_CHEAT_LOG (SUS_SCORE DESC, ADDED_AT ASC)
    WHERE RESOLVED = FALSE;

-- Admin: resolved by which moderator
CREATE INDEX IF NOT EXISTS idx_anti_cheat_resolved_by
    ON ANTI_CHEAT_LOG (RESOLVED_BY)
    WHERE RESOLVED_BY IS NOT NULL;

-- Join TIME_CONTROL → GAME_MODE
CREATE INDEX IF NOT EXISTS idx_time_control_game_mode_id
    ON TIME_CONTROL (GAME_MODE_ID);


-- VIEWS

-- Purpose : drive a per-player, per-game-mode ELO line chart.
CREATE OR REPLACE VIEW vw_player_rating_history AS
SELECT
    -- Identity
    ml.player_id,
    a.username,

    -- Game context
    ml.match_id,
    gm.name                                         AS game_mode,
    ml.player_side,

    -- Opponent
    CASE
        WHEN ml.player_side = 'w' THEN m.black_id
        ELSE m.white_id
    END                                             AS opponent_id,

    -- Result from this player's perspective
    CASE
        WHEN m.result = 'draw'                                               THEN 'draw'
        WHEN (ml.player_side = 'w' AND m.result = 'white')
          OR (ml.player_side = 'b' AND m.result = 'black')                  THEN 'win'
        ELSE                                                                      'loss'
    END                                             AS player_result,

    -- ELO timeline (the three columns you bind to your chart)
    ml.elo_before,
    ml.elo_shift,
    (ml.elo_before + ml.elo_shift)                  AS elo_after,

    -- Timestamps
    m.started_at,
    ml.ended_at

FROM match_log    ml
JOIN match        m  ON m.id  = ml.match_id
JOIN time_control tc ON tc.id = m.time_control_id
JOIN game_mode    gm ON gm.id = tc.game_mode_id
JOIN account      a  ON a.id  = ml.player_id
-- Human players only (excludes engine rows from MATCH_LOG)
WHERE EXISTS (
    SELECT 1 FROM player_account WHERE id = ml.player_id
);

-- Purpose : current ELO snapshot for every player across all
--           game modes — used by profile pages and leaderboards.
CREATE OR REPLACE VIEW vw_player_current_ratings AS
SELECT
    us.user_id                              AS player_id,
    a.username,
    gm.name                                AS game_mode,
    us.elo,
    us.n_wins,
    us.n_losses,
    us.n_draws,
    (us.n_wins + us.n_losses + us.n_draws) AS total_games
FROM user_stats  us
JOIN game_mode   gm ON gm.id = us.game_mode_id
JOIN account     a  ON a.id  = us.user_id;


-- drop table if exists ANTI_CHEAT_LOG;
-- drop table if exists BAN;
-- drop table if exists FRIEND_REQUEST;
-- drop table if exists FOLLOWER;
-- drop table if exists FRIENDSHIP;
-- drop table if exists USER_SESSION_LOG;
-- drop table if exists USER_STATS;
-- drop table if exists USER_PROFILE;
-- drop table if exists GAME_SEEK;
-- drop table if exists MATCH_LOG;
-- drop table if exists MATCH_STATE;
-- drop table if exists MATCH;
-- drop table if exists TIME_CONTROL;
-- drop table if exists GAME_MODE;
-- drop table if exists ADMIN_ACCOUNT;
-- drop table if exists ENGINE_ACCOUNT;
-- drop table if exists PLAYER_ACCOUNT;
-- drop table if exists PLAYABLE_ACCOUNT;
-- drop table if exists ACCOUNT;
-- drop extension if exists "pgcrypto";