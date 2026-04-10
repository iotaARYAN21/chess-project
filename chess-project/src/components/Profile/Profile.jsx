import React, { useEffect, useState } from 'react'
import './profile.css'

const Profile = () => {

  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const username = localStorage.getItem('username')

    if (!username) {
      setError("No user logged in")
      setLoading(false)
      return
    }

    async function fetchProfile() {
      try {
        const res = await fetch(`http://localhost:8000/users/${username}`)

        const data = await res.json()

        if (!res.ok) {
          setError(data.detail || "Failed to load profile")
          return
        }

        setProfile(data)
      } catch (err) {
        setError("Server error")
      } finally {
        setLoading(false)
      }
    }

    fetchProfile()
  }, [])

  if (loading) return <h2>Loading...</h2>
  if (error) return <h2 style={{color:'red'}}>{error}</h2>

  return (
    <div className="profile-container">

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

      <div className="rating-graph">
        <h2>Rating Graph</h2>
        <p>(Hook this to stats endpoint later)</p>
      </div>

    </div>
  )
}

export default Profile