import React, { useMemo, useState, useEffect, useRef, useCallback } from 'react';
import { Chess } from 'chess.js';
import { Chessboard } from 'react-chessboard';
import { useLocation, useNavigate } from 'react-router-dom';
import './gameboard.css';

const fmt = (ms) => {
  const total = Math.max(0, Math.floor(ms / 1000));
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
};

const GameBoard = () => {
  const { state }                 = useLocation();
  const { game_id, opponentName } = state ?? {};
  const navigate                  = useNavigate();

  const [game, setGame]           = useState(() => new Chess());
  const [username, setUsername]   = useState(null);
  const [boardSize, setBoardSize] = useState(480);
  const [moves, setMoves]         = useState([]);
  const [status, setStatus]       = useState('active');
  const [result, setResult]       = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [whiteMs, setWhiteMs]     = useState(null);
  const [blackMs, setBlackMs]     = useState(null);

  const playerColor = 'white';
  const tickRef     = useRef(null);
  const turnRef     = useRef(game.turn());
  const moveListRef = useRef(null);
  const wsRef       = useRef(null);

  // ── board size ─────────────────────────────────────────
  useEffect(() => {
    const calc = () => {
      const size = Math.min(window.innerHeight * 0.72, window.innerWidth * 0.5, 560);
      setBoardSize(Math.floor(size));
    };
    calc();
    window.addEventListener('resize', calc);
    return () => window.removeEventListener('resize', calc);
  }, []);

  // ── fetch username ─────────────────────────────────────
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return;
    fetch('http://localhost:8000/me', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((d) => setUsername(d.username))
      .catch(console.error);
  }, []);

  // ── initial match fetch ────────────────────────────────
  useEffect(() => {
    if (!game_id) return;
    const token = localStorage.getItem('token');

    fetch(`http://localhost:8000/match/${game_id}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((d) => {
        if (d.fen) setGame(new Chess(d.fen));
        if (d.moves) setMoves(d.moves);
        if (d.status) setStatus(d.status);
        if (d.result) setResult(d.result);
        if (d.white_time_remaining_ms != null) setWhiteMs(d.white_time_remaining_ms);
        if (d.black_time_remaining_ms != null) setBlackMs(d.black_time_remaining_ms);
      })
      .catch(console.error);
  }, [game_id]);

  // ── clock ticking ──────────────────────────────────────
  useEffect(() => {
    clearInterval(tickRef.current);
    if (status !== 'active' || whiteMs == null) return;

    tickRef.current = setInterval(() => {
      if (turnRef.current === 'w') {
        setWhiteMs((ms) => Math.max(0, ms - 100));
      } else {
        setBlackMs((ms) => Math.max(0, ms - 100));
      }
    }, 100);

    return () => clearInterval(tickRef.current);
  }, [status, whiteMs]);

  // ── sync turn ──────────────────────────────────────────
  useEffect(() => {
    turnRef.current = game.turn();
  }, [game]);

  // ── websocket ──────────────────────────────────────────
  useEffect(() => {
    if (!game_id) return;
    if (wsRef.current) return;

    const token = localStorage.getItem('token');
    const ws = new WebSocket(`ws://localhost:8000/match/ws/${game_id}?token=${token}`);
    wsRef.current = ws;

    ws.onmessage = (e) => {
      const { type, payload } = JSON.parse(e.data);

      if (type === 'MOVE_MADE') {
        setGame(new Chess(payload.fen));
        setWhiteMs(payload.white_time_remaining_ms);
        setBlackMs(payload.black_time_remaining_ms);

        if (payload.san) {
          setMoves((prev) => {
            const last = prev[prev.length - 1];
            if (last && last.uci === payload.uci) return prev;
            return [...prev, { san: payload.san, uci: payload.uci }];
          });
        }

        if (payload.status === 'completed') {
          setStatus('completed');
          setResult(payload.result);
          clearInterval(tickRef.current);
        }
      }
    };

    ws.onerror = console.error;

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [game_id]);

  // ── send move ──────────────────────────────────────────
  const sendMove = useCallback(async (uci) => {
    const token = localStorage.getItem('token');
    setSubmitting(true);

    try {
      const res = await fetch(`http://localhost:8000/match/${game_id}/move`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ uci }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? 'Move rejected');
      }
    } catch (e) {
      console.error(e);
    } finally {
      setSubmitting(false);
    }
  }, [game_id]);

  // ── drop handler (OPTIMISTIC) ─────────────────────────
  const boardOptions = useMemo(() => ({
    id: 'game-board',
    position: game.fen(),
    allowDragging: status === 'active' && !submitting && game.turn() === 'w',
    onPieceDrop: ({ sourceSquare, targetSquare }) => {
      if (!targetSquare) return false;

      const temp = new Chess(game.fen());
      const move = temp.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: 'q'
      });

      if (!move) return false;

      // ✅ instant UI update
      setGame(temp);
      setMoves(prev => [...prev, { san: move.san, uci: move.from + move.to }]);

      sendMove(move.from + move.to + (move.promotion ?? ''));

      return true;
    },
  }), [game, status, submitting, sendMove]);

  // ── result helpers ─────────────────────────────────────
  const resultIcon  = result === 'draw' ? '½' : result === playerColor ? '♔' : '♚';
  const resultLabel = result === 'draw' ? 'Draw' : result === playerColor ? 'You Won' : 'You Lost';
  const resultSub   = result === 'draw'
    ? 'The game ended in a draw'
    : result === playerColor
    ? 'Well played!'
    : 'Better luck next time';

  const movePairs = [];
  for (let i = 0; i < moves.length; i += 2) {
    movePairs.push({
      num: Math.floor(i / 2) + 1,
      w: moves[i]?.san,
      b: moves[i + 1]?.san,
    });
  }

  useEffect(() => {
    if (moveListRef.current) {
      moveListRef.current.scrollTop = moveListRef.current.scrollHeight;
    }
  }, [moves]);

  const turnLabel = status === 'active'
    ? game.turn() === 'w'
      ? 'Your turn'
      : `${opponentName ?? 'Engine'} is thinking…`
    : null;

  return (
    <div className="game-layout">

      <div className="side-panel side-panel--left">
        <div className="info-card">
          <span className="info-card__label">Match</span>
          <span className="info-card__value">
            {game_id ? game_id.slice(0, 8) + '…' : '—'}
          </span>
        </div>

        <div className="info-card">
          <span className="info-card__label">Move</span>
          <span className="info-card__value">{moves.length}</span>
        </div>

        <div className="info-card">
          <span className="info-card__label">Status</span>
          <span className={`info-card__value info-card__value--status ${status === 'active' ? 'active' : 'done'}`}>
            {status}
          </span>
        </div>

        {turnLabel && (
          <div className="turn-indicator">
            <span className={`turn-dot ${game.turn() === 'w' ? 'turn-dot--white' : 'turn-dot--black'}`} />
            <span className="turn-label">{turnLabel}</span>
          </div>
        )}
      </div>

      <div className="game-main">

        <div className="player-bar">
          <div className="player-bar__identity">
            <div className="player-bar__icon">♟</div>
            <span className="player-bar__name">{opponentName ?? 'Opponent'}</span>
            <span className="player-bar__badge">Engine</span>
          </div>

          <div className={`clock ${game.turn() === 'b' && status === 'active' ? 'clock--active' : 'clock--inactive'}`}>
            {blackMs != null ? fmt(blackMs) : '—'}
          </div>
        </div>

        <div className="board-wrap" style={{ width: boardSize }}>
          <Chessboard options={boardOptions} />

          {status === 'completed' && (
            <div className="result-overlay">
              <div className="result-box">
                <span className="result-box__icon">{resultIcon}</span>
                <span className="result-box__label">{resultLabel}</span>
                <span className="result-box__sub">{resultSub}</span>

                <div className="result-box__actions">
                  <button onClick={() => navigate('/lobby')} className="result-btn result-btn--primary">
                    New Game
                  </button>
                  <button onClick={() => navigate('/dashboard')} className="result-btn result-btn--ghost">
                    Dashboard
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="game-controls">
          <button className="control-btn control-btn--ghost" disabled>½ Offer Draw</button>
          <button className="control-btn control-btn--danger" disabled>⚑ Resign</button>
        </div>

        <div className="player-bar player-bar--you">
          <div className="player-bar__identity">
            <div className="player-bar__icon player-bar__icon--you">♙</div>
            <span className="player-bar__name">{username ?? '...'}</span>
            <span className="player-bar__badge player-bar__badge--you">You</span>
          </div>

          <div className={`clock ${game.turn() === 'w' && status === 'active' ? 'clock--active' : 'clock--inactive'}`}>
            {whiteMs != null ? fmt(whiteMs) : '—'}
          </div>
        </div>

      </div>

      <div className="side-panel side-panel--right">
        <div className="move-panel">
          <div className="move-panel__header">Move History</div>

          <div className="move-panel__list" ref={moveListRef}>
            {movePairs.length === 0 && (
              <p className="move-panel__empty">No moves yet</p>
            )}

            {movePairs.map(({ num, w, b }) => (
              <div key={num} className={`move-row ${num % 2 === 0 ? 'move-row--even' : ''}`}>
                <span className="move-row__num">{num}.</span>
                <span className="move-row__san">{w}</span>
                <span className="move-row__san move-row__san--black">{b ?? ''}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

    </div>
  );
};

export default GameBoard;