import React, { useEffect, useState } from 'react'
import './profile.css'

const Profile = () => {

  const [profile, setProfile] = useState(null)
  const [stats, setStats] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const username = localStorage.getItem('username')

    if (!username) {
      setError("No user logged in")
      setLoading(false)
      return
    }

    async function fetchData() {
      try {
        // 🔹 Fetch profile
        const profileRes = await fetch(`http://localhost:8000/users/${username}`)
        const profileData = await profileRes.json()

        if (!profileRes.ok) {
          setError(profileData.detail || "Failed to load profile")
          return
        }

        setProfile(profileData)

        // 🔹 Fetch stats
        const statsRes = await fetch(`http://localhost:8000/users/${username}/stats`)
        const statsData = await statsRes.json()

        if (statsRes.ok) {
          setStats(statsData)
        }

      } catch (err) {
        setError("Server error")
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) return <h2>Loading...</h2>
  if (error) return <h2 style={{color:'red'}}>{error}</h2>

  return (
    <div className="profile-container">

      {/* -------- TOP SECTION -------- */}
      <div className="top-section">
        <img 
          src={profile.avatar_url || "https://via.placeholder.com/150"} 
          alt="Profile" 
          className="profile-image" 
        />

        <div className="player-info">
          <h2>@{profile.username}</h2>
          <p>{profile.bio || "No bio yet"}</p>

          <div className="stats">
            <span>Followers: {profile.n_followers}</span>
            <span>Friends: {profile.n_friends}</span>
          </div>
        </div>
      </div>

      {/* -------- ELO STATS -------- */}
      <div className="elo-section">
        <h2>Ratings</h2>

        <div className="elo-grid">
          {stats.map((s, index) => (
            <div key={index} className="elo-card">
              <h3>{s.game_mode.toUpperCase()}</h3>
              <p className="elo">{s.elo}</p>

              <div className="wl">
                <span>W: {s.wins}</span>
                <span>L: {s.losses}</span>
                <span>D: {s.draws}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* -------- GRAPH -------- */}
      <div className="rating-graph">
        <h2>Rating Graph</h2>
        <p>(Hook this to chart later)</p>
      </div>

    </div>
  )
}

export default Profile