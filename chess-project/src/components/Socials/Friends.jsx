import React, { useEffect, useState } from 'react'
import './friends.css'

const Friends = () => {

  const [friends, setFriends] = useState([])
  const [requests, setRequests] = useState([])
  const [followers, setFollowers] = useState(0)
  const [searchUser, setSearchUser] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // 🔥 NEW STATE
  const [selectedFriend, setSelectedFriend] = useState(null)
  const [selectedStats, setSelectedStats] = useState([])
  const [showProfile, setShowProfile] = useState(false)

  const username = localStorage.getItem('username')

  useEffect(() => {
    async function fetchData() {
      try {
        const [fRes, rRes, pRes] = await Promise.all([
          fetch("http://localhost:8000/social/friends"),
          fetch("http://localhost:8000/social/friend-requests"),
          fetch(`http://localhost:8000/users/${username}`)
        ])

        if (fRes.ok) setFriends(await fRes.json())
        if (rRes.ok) setRequests(await rRes.json())

        const pData = await pRes.json()
        if (pRes.ok) setFollowers(pData.n_followers)

      } catch {
        setError("Failed to load data")
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [username])

  // -------- VIEW FRIEND PROFILE --------

  const handleViewFriend = async (friendUsername) => {
    try {
      const [profileRes, statsRes] = await Promise.all([
        fetch(`http://localhost:8000/users/${friendUsername}`),
        fetch(`http://localhost:8000/users/${friendUsername}/stats`)
      ])

      if (profileRes.ok) {
        const profileData = await profileRes.json()
        setSelectedFriend(profileData)
      }

      if (statsRes.ok) {
        const statsData = await statsRes.json()
        setSelectedStats(statsData)
      }

      setShowProfile(true)

    } catch {
      alert("Failed to load friend profile")
    }
  }

  const handleCloseProfile = () => {
    setShowProfile(false)
    setSelectedFriend(null)
    setSelectedStats([])
  }

  // -------- ACTIONS --------

  const handleAccept = async (id) => {
    const req = requests.find(r => r.id === id)

    const res = await fetch(`http://localhost:8000/social/friend-request/${id}/accept`, {
      method: "POST"
    })

    if (!res.ok) {
      alert("Failed to accept request")
      return
    }

    setRequests(prev => prev.filter(r => r.id !== id))

    if (req) {
      const userRes = await fetch(`http://localhost:8000/users/${req.from_username}`)
      
      if (userRes.ok) {
        const userData = await userRes.json()

        setFriends(prev => [
          ...prev,
          {
            username: userData.username,
            bio: userData.bio
          }
        ])
      }
    }
  }

  const handleDecline = async (id) => {
    await fetch(`http://localhost:8000/social/friend-request/${id}/decline`, {
      method: "POST"
    })

    setRequests(prev => prev.filter(r => r.id !== id))
  }

  const handleSendRequest = async () => {
    if (!searchUser) return

    const res = await fetch("http://localhost:8000/social/friend-request", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ to_username: searchUser })
    })

    const data = await res.json()

    if (!res.ok) {
      alert(data.detail || "Failed")
      return
    }

    alert("Friend request sent!")
    setSearchUser('')
  }

  const handleRemoveFriend = async (username) => {
    const confirmDelete = window.confirm(`Remove ${username} from friends?`)
    if (!confirmDelete) return

    const res = await fetch(`http://localhost:8000/social/friends/${username}`, {
      method: "DELETE"
    })

    if (res.ok) {
      setFriends(prev => prev.filter(f => f.username !== username))

      // 🔥 If viewing same friend, close panel
      if (selectedFriend?.username === username) {
        handleCloseProfile()
      }

    } else {
      alert("Failed to remove friend")
    }
  }

  if (loading) return <h2>Loading...</h2>
  if (error) return <h2 style={{ color: 'red' }}>{error}</h2>

  return (
    <div className="friends-container">

      {/* LEFT SIDE */}
      <div className="left-panel">

        {/* SEARCH */}
        <div className="search-box">
          <input
            type="text"
            placeholder="Enter username..."
            value={searchUser}
            onChange={(e) => setSearchUser(e.target.value)}
          />
          <button onClick={handleSendRequest}>Send Request</button>
        </div>

        {/* FRIENDS */}
        <div className="friends-section">
          <h2>Your Friends</h2>

          {friends.length === 0 && <p>No friends yet</p>}

          <div className="friends-grid">
            {friends.map((f, index) => (
              <div 
                key={index} 
                className="friend-card"
                onClick={() => handleViewFriend(f.username)}
              >
                <h3>{f.username}</h3>

              </div>
            ))}
          </div>
        </div>

        {/* 🔥 FRIEND PROFILE WIDGET */}
        {showProfile && selectedFriend && (
          <div className="friend-profile-widget">

            <button className="close-btn" onClick={handleCloseProfile}>✖</button>

            <div className="top-section">
              <div 
                className="avatar-circle"
                style={{ backgroundColor: selectedFriend.avatar_url || "#4CAF50" }}
              >
                {selectedFriend.username?.charAt(0).toUpperCase()}
              </div>

              <div className="player-info">
                <h2>@{selectedFriend.username}</h2>
                <p>{selectedFriend.bio || "No bio"}</p>
              </div>
            </div>

            <div className="elo-grid">
              {selectedStats.map((s, index) => (
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

            <button 
              className="remove-btn"
              onClick={() => handleRemoveFriend(selectedFriend.username)}
            >
              Unfriend
            </button>

          </div>
        )}

      </div>

      {/* RIGHT SIDE */}
      <div className="right-panel">

        <h2>Notifications</h2>

        {requests.length === 0 && <p>No pending requests</p>}

        {requests.map((r) => (
          <div key={r.id} className="request-card">
            
            <div className="request-info">
              <div className="avatar">
                {r.from_username?.charAt(0).toUpperCase()}
              </div>

              <div>
                <h4>{r.from_username || "Unknown User"}</h4>
                <p>sent you a friend request</p>
              </div>
            </div>

            <div className="actions">
              <button className="accept" onClick={() => handleAccept(r.id)}>Accept</button>
              <button className="decline" onClick={() => handleDecline(r.id)}>Decline</button>
            </div>

          </div>
        ))}

      </div>

    </div>
  )
}

export default Friends