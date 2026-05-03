import React, { useEffect, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import './profile.css'

const MODES = ['bullet', 'blitz', 'rapid', 'classical']

const MODE_COLORS = {
  bullet:    '#FF6B6B',
  blitz:     '#FFC107',
  rapid:     '#4CAF50',
  classical: '#64B5F6',
}

const RESULT_SYMBOLS = { win: '●', loss: '×', draw: '–' }

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="chart-tooltip">
      <p className="tooltip-date">{new Date(label).toLocaleDateString()}</p>
      <p style={{ color: MODE_COLORS[d.game_mode] }}>
        {d.game_mode.toUpperCase()}
      </p>
      <p>ELO: <strong>{d.elo_after}</strong></p>
      <p style={{ color: d.player_result === 'win' ? '#4CAF50' : d.player_result === 'loss' ? '#FF6B6B' : '#aaa' }}>
        {d.player_result.toUpperCase()} ({d.elo_shift >= 0 ? '+' : ''}{d.elo_shift})
      </p>
    </div>
  )
}

const Profile = () => {
  const [profile,       setProfile]       = useState(null)
  const [stats,         setStats]         = useState([])
  const [history,       setHistory]       = useState({})   // { mode: [{...}] }
  const [activeMode,    setActiveMode]    = useState('blitz')
  const [loading,       setLoading]       = useState(true)
  const [error,         setError]         = useState('')
  const [showPicker,    setShowPicker]    = useState(false)

  useEffect(() => {
    const username = localStorage.getItem('username')
    if (!username) { setError("No user logged in"); setLoading(false); return }

    const headers = {
      "Authorization": `Bearer ${localStorage.getItem('token')}`,
      "Content-Type": "application/json"
    }

    async function fetchData() {
      try {
        const [profileRes, statsRes, historyRes] = await Promise.all([
          fetch(`http://localhost:8000/users/${username}`,               { headers }),
          fetch(`http://localhost:8000/users/${username}/stats`,         { headers }),
          fetch(`http://localhost:8000/users/${username}/rating-history`,{ headers }),
        ])

        const profileData = await profileRes.json()
        if (!profileRes.ok) { setError(profileData.detail || "Failed to load profile"); return }
        setProfile(profileData)

        if (statsRes.ok)   setStats(await statsRes.json())

        if (historyRes.ok) {
          const raw = await historyRes.json()
          // Split flat list into per-mode arrays, add a JS Date for recharts
          const grouped = {}
          MODES.forEach(m => { grouped[m] = [] })
          raw.forEach(row => {
            const mode = row.game_mode
            if (grouped[mode]) {
              grouped[mode].push({ ...row, ts: new Date(row.ended_at).getTime() })
            }
          })
          setHistory(grouped)
          // Default to the first mode that actually has data
          const firstWithData = MODES.find(m => grouped[m].length > 0)
          if (firstWithData) setActiveMode(firstWithData)
        }

      } catch {
        setError("Server error")
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  const updateAvatar = async (color) => {
    const username = localStorage.getItem('username')
    const res = await fetch(`http://localhost:8000/users/${username}/profile`, {
      method: "PUT",
      headers: {
        "Authorization": `Bearer ${localStorage.getItem('token')}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ avatar_url: color })
    })
    if (res.ok) setProfile(prev => ({ ...prev, avatar_url: color }))
    else alert("Failed to update avatar")
  }

  if (loading) return <h2>Loading...</h2>
  if (error)   return <h2 style={{ color: 'red' }}>{error}</h2>

  const chartData = history[activeMode] ?? []

  // Y-axis domain with a little padding
  const elos     = chartData.map(d => d.elo_after)
  const eloMin   = elos.length ? Math.min(...elos) - 30 : 800
  const eloMax   = elos.length ? Math.max(...elos) + 30 : 2000

  return (
    <div className="profile-container">

      {/* -------- TOP SECTION -------- */}
      <div className="top-section">
        <div
          className="avatar-circle"
          style={{ backgroundColor: profile.avatar_url || "#4CAF50" }}
          onClick={() => setShowPicker(prev => !prev)}
        >
          {profile.username?.charAt(0).toUpperCase()}
        </div>

        {showPicker && (
          <div className="avatar-picker">
            {["#4CAF50", "#2196F3", "#FF5722", "#9C27B0", "#FFC107"].map(color => (
              <div
                key={color}
                className="color-dot"
                style={{ backgroundColor: color }}
                onClick={() => { updateAvatar(color); setShowPicker(false) }}
              />
            ))}
          </div>
        )}

        <div className="player-info">
          <h2>@{profile.username}</h2>
          <p>{profile.bio || "No bio yet"}</p>
          <div className="stats">
            <span>Friends: {profile.n_friends}</span>
          </div>
        </div>
      </div>

      {/* -------- ELO CARDS -------- */}
      <div className="elo-section">
        <h2>Ratings</h2>
        <div className="elo-grid">
          {stats.map((s, i) => (
            <div
              key={i}
              className={`elo-card${activeMode === s.game_mode ? ' elo-card--active' : ''}`}
              onClick={() => setActiveMode(s.game_mode)}
            >
              <h3>{s.game_mode.toUpperCase()}</h3>
              <p className="elo" style={{ color: MODE_COLORS[s.game_mode] }}>{s.elo}</p>
              <div className="wl">
                <span>W: {s.wins}</span>
                <span>L: {s.losses}</span>
                <span>D: {s.draws}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* -------- RATING GRAPH -------- */}
      <div className="rating-graph">
        <div className="graph-header">
          <h2>Rating History</h2>
          <div className="mode-tabs">
            {MODES.map(mode => (
              <button
                key={mode}
                className={`mode-tab${activeMode === mode ? ' mode-tab--active' : ''}`}
                style={activeMode === mode ? { borderColor: MODE_COLORS[mode], color: MODE_COLORS[mode] } : {}}
                onClick={() => setActiveMode(mode)}
              >
                {mode.charAt(0).toUpperCase() + mode.slice(1)}
                {history[mode]?.length ? ` (${history[mode].length})` : ''}
              </button>
            ))}
          </div>
        </div>

        {chartData.length === 0 ? (
          <p className="no-data">No {activeMode} games played yet.</p>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
              <XAxis
                dataKey="ts"
                type="number"
                scale="time"
                domain={['dataMin', 'dataMax']}
                tickFormatter={ts => new Date(ts).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                stroke="rgba(255,255,255,0.4)"
                tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 11 }}
              />
              <YAxis
                domain={[eloMin, eloMax]}
                stroke="rgba(255,255,255,0.4)"
                tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 11 }}
                width={45}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="elo_after"
                stroke={MODE_COLORS[activeMode]}
                strokeWidth={2}
                dot={({ cx, cy, payload }) => (
                  <circle
                    key={`${cx}-${cy}`}
                    cx={cx} cy={cy} r={4}
                    fill={payload.player_result === 'win'  ? '#4CAF50'
                        : payload.player_result === 'loss' ? '#FF6B6B'
                        : '#aaa'}
                    stroke="none"
                  />
                )}
                activeDot={{ r: 6, strokeWidth: 0 }}
                name="ELO"
              />
            </LineChart>
          </ResponsiveContainer>
        )}

        <div className="graph-legend">
          <span><span className="legend-dot" style={{background:'#4CAF50'}}/>Win</span>
          <span><span className="legend-dot" style={{background:'#FF6B6B'}}/>Loss</span>
          <span><span className="legend-dot" style={{background:'#aaa'}}/>Draw</span>
        </div>
      </div>

    </div>
  )
}

export default Profile