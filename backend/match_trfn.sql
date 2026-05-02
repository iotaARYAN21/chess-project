-- ==========================================
-- 1. INITIALIZATION LOGIC
-- ==========================================

CREATE OR REPLACE FUNCTION fn_initialize_match_state()
RETURNS TRIGGER AS $$
DECLARE
    v_base_time_ms INT;
BEGIN
    IF NEW.status != 'active' THEN
        RETURN NEW;
    END IF;

    SELECT (base_time * 1000) INTO v_base_time_ms
    FROM time_control
    WHERE id = NEW.time_control_id;

    IF v_base_time_ms IS NULL THEN
        RAISE EXCEPTION 'Initialization failed: time_control_id % not found.', NEW.time_control_id;
    END IF;

    INSERT INTO match_state (
        match_id, 
        fen, 
        white_time_remaining_ms, 
        black_time_remaining_ms, 
        turn_started_at, 
        move_number, 
        move_history
    ) VALUES (
        NEW.id, 
        'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', 
        v_base_time_ms, 
        v_base_time_ms, 
        NEW.started_at, 
        0, 
        '{}'
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_initialize_match_state
AFTER INSERT ON match
FOR EACH ROW EXECUTE FUNCTION fn_initialize_match_state();

-- ==========================================
-- 2. HELPER: UPSERT PLAYER STATISTICS
-- ==========================================

CREATE OR REPLACE FUNCTION fn_upsert_player_stats(
    p_user_id UUID,
    p_mode_id UUID,
    p_result VARCHAR(10),
    p_is_white BOOLEAN,
    p_elo_shift INT
) RETURNS VOID AS $$
DECLARE
    v_win INT := 0;
    v_loss INT := 0;
    v_draw INT := 0;
BEGIN
    IF p_result = 'draw' THEN
        v_draw := 1;
    ELSIF (p_is_white AND p_result = 'white') OR (NOT p_is_white AND p_result = 'black') THEN
        v_win := 1;
    ELSE
        v_loss := 1;
    END IF;

    INSERT INTO USER_STATS (USER_ID, GAME_MODE_ID, ELO, N_WINS, N_LOSSES, N_DRAWS)
    VALUES (p_user_id, p_mode_id, 1200 + p_elo_shift, v_win, v_loss, v_draw)
    ON CONFLICT (USER_ID, GAME_MODE_ID) DO UPDATE SET
        ELO = USER_STATS.ELO + p_elo_shift,
        N_WINS = USER_STATS.N_WINS + v_win,
        N_LOSSES = USER_STATS.N_LOSSES + v_loss,
        N_DRAWS = USER_STATS.N_DRAWS + v_draw;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- 3. MASTER OUTCOME TRIGGER
-- ==========================================

CREATE OR REPLACE FUNCTION fn_on_match_completion()
RETURNS TRIGGER AS $$
DECLARE
    v_history TEXT[];
    v_mode_id UUID;
BEGIN
-- NOTE: already handling engines here i.e only upserting player stats
    IF (NEW.status = 'completed' AND OLD.status = 'active') THEN
        
        -- A. DATA GATHERING
        SELECT game_mode_id INTO v_mode_id 
        FROM TIME_CONTROL WHERE id = NEW.time_control_id;

        SELECT move_history INTO v_history 
        FROM match_state WHERE match_id = NEW.id;

        -- B. SNAPSHOT ARCHIVAL
        NEW.final_pgn := ARRAY_TO_STRING(v_history, ' ');

        -- C. PERSISTENT LOGGING
        INSERT INTO MATCH_LOG (match_id, player_id, player_side, elo_before, elo_shift, ended_at)
        VALUES 
            (NEW.id, NEW.white_id, 'w', NEW.white_elo_initial, NEW.white_elo_shift, NEW.ended_at),
            (NEW.id, NEW.black_id, 'b', NEW.black_elo_initial, NEW.black_elo_shift, NEW.ended_at);

        -- D. CAREER STATISTICS (Humans Only)
        IF NEW.white_id IS NOT NULL AND EXISTS (SELECT 1 FROM PLAYER_ACCOUNT WHERE id = NEW.white_id) THEN
            PERFORM fn_upsert_player_stats(NEW.white_id, v_mode_id, NEW.result, TRUE, NEW.white_elo_shift);
        END IF;

        IF NEW.black_id IS NOT NULL AND EXISTS (SELECT 1 FROM PLAYER_ACCOUNT WHERE id = NEW.black_id) THEN
            PERFORM fn_upsert_player_stats(NEW.black_id, v_mode_id, NEW.result, FALSE, NEW.black_elo_shift);
        END IF;

        -- E. PURGE HOT DATA
        DELETE FROM match_state WHERE match_id = NEW.id;

    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_on_match_completion
BEFORE UPDATE ON match
FOR EACH ROW EXECUTE FUNCTION fn_on_match_completion();

-- ==========================================
-- 4. INTERFACE: MOVE HANDLER
-- ==========================================

CREATE OR REPLACE FUNCTION fn_handle_match_move(
    p_match_id UUID,
    p_move_number INT,
    p_uci TEXT,
    p_fen TEXT,
    p_white_ms INT,
    p_black_ms INT,
    p_status TEXT,
    p_next_turn_at TIMESTAMPTZ,
    p_result TEXT DEFAULT NULL,
    p_ended_at TIMESTAMPTZ DEFAULT NULL,
    p_white_elo_shift INT DEFAULT 0,
    p_black_elo_shift INT DEFAULT 0
) RETURNS VOID AS $$
BEGIN
    -- 1. Update Hot State
    UPDATE match_state 
    SET 
        fen = p_fen,
        white_time_remaining_ms = p_white_ms,
        black_time_remaining_ms = p_black_ms,
        turn_started_at = p_next_turn_at,
        move_number = p_move_number,
        move_history = ARRAY_APPEND(move_history, p_uci)
    WHERE match_id = p_match_id AND move_number = p_move_number - 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'CONCURRENCY_ERROR: Match state has changed or ended.';
    END IF;

    -- 2. Update Match (Triggers trg_on_match_completion if status is 'completed')
    IF p_status = 'completed' THEN
        UPDATE match 
        SET 
            status = 'completed', 
            result = p_result, 
            ended_at = p_ended_at,
            white_elo_shift = p_white_elo_shift,
            black_elo_shift = p_black_elo_shift,
            final_fen = p_fen
        WHERE id = p_match_id;
    END IF;
END;
$$ LANGUAGE plpgsql;