import React, { useMemo, useState, useEffect, useRef, useCallback } from 'react';
import { Chess } from 'chess.js';
import { Chessboard } from 'react-chessboard';
import { useLocation } from 'react-router-dom';
import './gameboard.css';

const fmt = (ms) => {
  const total = Math.max(0, Math.floor(ms / 1000));
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
};

const GameBoard = () => {
  const { state } = useLocation();
  const { game_id, opponentName } = state ?? {};

  const [game, setGame]               = useState(() => new Chess());
  const [username, setUsername]       = useState(null);
  const [boardSize, setBoardSize]     = useState(480);
  const [moves, setMoves]             = useState([]);          // { san, uci }
  const [status, setStatus]           = useState('active');    // active | completed
  const [result, setResult]           = useState(null);        // white | black | draw
  const [submitting, setSubmitting]   = useState(false);
  const [whiteMs, setWhiteMs]         = useState(null);
  const [blackMs, setBlackMs]         = useState(null);

  const playerColor = 'white'; // human is always white in bot games
  const tickRef     = useRef(null);
  const turnRef     = useRef(game.turn()); // 'w' | 'b'

  // ── board size ──────────────────────────────────────────────────────────────
  useEffect(() => {
    const calc = () => {
      const size = Math.min(window.innerHeight * 0.72, window.innerWidth * 0.55, 580);
      setBoardSize(Math.floor(size));
    };
    calc();
    window.addEventListener('resize', calc);
    return () => window.removeEventListener('resize', calc);
  }, []);

  // ── fetch username ───────────────────────────────────────────────────────────
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

  // ── fetch initial match state ────────────────────────────────────────────────
  useEffect(() => {
  if (!game_id) return;
  const token = localStorage.getItem('token');
  fetch(`http://localhost:8000/match/${game_id}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
    .then((r) => r.json())
    .then((d) => {
      if (d.fen)                      setGame(new Chess(d.fen));
      if (d.moves)                    setMoves(d.moves);
      if (d.status)                   setStatus(d.status);
      if (d.result)                   setResult(d.result);
      if (d.white_time_remaining_ms != null) setWhiteMs(d.white_time_remaining_ms);
      if (d.black_time_remaining_ms != null) setBlackMs(d.black_time_remaining_ms);
    })
    .catch(console.error);
}, [game_id]);

  // ── clock tick ───────────────────────────────────────────────────────────────
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

  // ── sync turn ref ────────────────────────────────────────────────────────────
  useEffect(() => {
    turnRef.current = game.turn();
  }, [game]);

  // ── websocket (receives engine moves) ───────────────────────────────────────
  useEffect(() => {
    if (!game_id) return;
    const token = localStorage.getItem('token');
    const ws = new WebSocket(`ws://localhost:8000/match/ws/${game_id}?token=${token}`);

    ws.onmessage = (e) => {
      const { type, payload } = JSON.parse(e.data);

      if (type === 'MOVE_MADE') {
        setGame(new Chess(payload.fen));
        setWhiteMs(payload.white_time_remaining_ms);
        setBlackMs(payload.black_time_remaining_ms);
        if (payload.san) setMoves((prev) => [...prev, { san: payload.san, uci: payload.uci }]);
        if (payload.status === 'completed') {
          setStatus('completed');
          setResult(payload.result);
          clearInterval(tickRef.current);
        }
      }

      if (type === 'ENGINE_ERROR') {
        console.error('Engine error:', payload.detail);
      }
    };

    ws.onerror = console.error;
    return () => ws.close();
  }, [game_id]);

  // ── send move to backend ─────────────────────────────────────────────────────
  const sendMove = useCallback(async (uci, gameCopy) => {
    const token = localStorage.getItem('token');
    setSubmitting(true);
    try {
      const res = await fetch(`http://localhost:8000/match/${game_id}/move`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ uci }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? 'Move rejected');
      }
      const data = await res.json();

      setWhiteMs(data.white_time_remaining_ms);
      setBlackMs(data.black_time_remaining_ms);
      setGame(new Chess(data.fen));

      if (data.san) {
        setMoves((prev) => [...prev, { san: data.san, uci: data.uci }]);
      }
      if (data.status === 'completed') {
        setStatus('completed');
        setResult(data.result);
        clearInterval(tickRef.current);
      }
    } catch (e) {
      console.error(e);
      setGame(new Chess(game.fen())); // revert
    } finally {
      setSubmitting(false);
    }
  }, [game_id, game]);

  // ── drop handler ─────────────────────────────────────────────────────────────
  const boardOptions = useMemo(() => ({
    id: 'game-board',
    position: game.fen(),
    allowDragging: status === 'active' && !submitting && game.turn() === 'w',
    onPieceDrop: ({ sourceSquare, targetSquare }) => {
      if (!targetSquare) return false;
      const gameCopy = new Chess(game.fen());
      try {
        const move = gameCopy.move({ from: sourceSquare, to: targetSquare, promotion: 'q' });
        if (!move) return false;
        setGame(gameCopy);
        sendMove(move.from + move.to + (move.promotion ?? ''), gameCopy);
        return true;
      } catch {
        return false;
      }
    },
  }), [game, status, submitting, sendMove]);

  // ── result label ─────────────────────────────────────────────────────────────
  const resultLabel = result === 'draw'
    ? 'Draw'
    : result === playerColor
    ? 'You won'
    : 'You lost';

  // ── pair moves for table ─────────────────────────────────────────────────────
  const movePairs = [];
  for (let i = 0; i < moves.length; i += 2) {
    movePairs.push({ num: Math.floor(i / 2) + 1, w: moves[i]?.san, b: moves[i + 1]?.san });
  }

  return (
    <div className="game-layout">

      <div className="game-main">

        {/* Opponent */}
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

        {/* Board */}
        <div className="board-wrap" style={{ width: boardSize }}>
          <Chessboard options={boardOptions} />
          {status === 'completed' && (
            <div className="result-overlay">
              <div className="result-box">
                <span className="result-box__label">{resultLabel}</span>
                <span className="result-box__sub">
                  {result === 'draw' ? 'The game ended in a draw' : result === playerColor ? 'Congratulations!' : 'Better luck next time'}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* You */}
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

      {/* Move history */}
      <div className="move-panel">
        <div className="move-panel__header">Moves</div>
        <div className="move-panel__list">
          {movePairs.map(({ num, w, b }) => (
            <div key={num} className="move-row">
              <span className="move-row__num">{num}.</span>
              <span className="move-row__san">{w}</span>
              <span className="move-row__san move-row__san--black">{b ?? ''}</span>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
};

export default GameBoard;