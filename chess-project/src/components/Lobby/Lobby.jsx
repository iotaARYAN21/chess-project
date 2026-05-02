import React, { useState, useEffect } from 'react';
import './lobby.css';
import { useNavigate } from 'react-router-dom';

const FORMAT_TIME = (s) => s < 60 ? `${s}s` : `${Math.floor(s / 60)}m`;
const MODE_ICONS = { bullet: '🔫', blitz: '⚡', rapid: '⏱️', classical: '♟️' };

function TimeControlCard({ mode_name, base_time, incr_time, disabled, onClick }) {
  const timeLabel = incr_time > 0
    ? `${FORMAT_TIME(base_time)} + ${incr_time}s`
    : FORMAT_TIME(base_time);

  return (
    <div className={`game-card ${disabled ? 'game-card--disabled' : ''}`} onClick={disabled ? undefined : onClick}>
      <span className="game-card__icon">{MODE_ICONS[mode_name] ?? '🎮'}</span>
      <h3 className="game-card__mode">{mode_name.toUpperCase()}</h3>
      <p className="game-card__time">{timeLabel}</p>
    </div>
  );
}

export default function Lobby() {
  const [gameModes, setGameModes] = useState([]);
  const [botUsername, setBotUsername] = useState('stockfish_16');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const controller = new AbortController();
    fetch('http://localhost:8000/modes', { signal: controller.signal })
      .then((res) => res.json())
      .then((data) => setGameModes(data.game_modes ?? []))
      .catch((err) => { if (err.name !== 'AbortError') setError(err.message); });
    return () => controller.abort();
  }, []);

  const handleSelect = async (timeControlId) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) throw new Error('Please log in again (token not found)');

      const res = await fetch('http://localhost:8000/api/seek', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json', 
            Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({ 
            time_control_id: timeControlId, 
            bot_username: botUsername 
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? 'Failed to start game');
      }

        const data = await res.json();
        navigate('/gameboard', {
            state: {
                game_id: data.game_id,
                user_id: data.user_id,
                opponentName: data.opponent_name,
                opponentId: data.opponent_id,
            },
        });
    } catch (e) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="lobby">
      <div className="lobby-intro">
        <h1>Quick Pair</h1>
        <p>Choose your battlefield. Ratings updated in real-time.</p>
        <div className="bot-selector">
            <label>Opponent</label>
            <div className="bot-selector__options">
                {[
                { value: 'stockfish_16', label: 'Stockfish 16', rating: '3200' },
                { value: 'komodo_14',    label: 'Komodo 14',    rating: '3000' },
                { value: 'GM_Magnus90',  label: 'GM Magnus',    rating: '2850' },
                ].map((bot) => (
                <button
                    key={bot.value}
                    className={`bot-option ${botUsername === bot.value ? 'bot-option--active' : ''}`}
                    onClick={() => setBotUsername(bot.value)}
                    disabled={loading}
                >
                    <span className="bot-option__name">{bot.label}</span>
                    <span className="bot-option__rating">{bot.rating}</span>
                </button>
                ))}
            </div>
            </div>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="games">
        {gameModes.flatMap((mode) =>
          mode.time_controls.map((tc) => (
            <TimeControlCard
              key={tc.id}
              mode_name={mode.name}
              base_time={tc.base_time}
              incr_time={tc.incr_time}
              disabled={loading}
              onClick={() => handleSelect(tc.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}