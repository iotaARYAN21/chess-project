import React, { useEffect, useState } from 'react'
import './friends.css'

const Friends = () => {

  const [friends, setFriends] = useState([])
  const [requests, setRequests] = useState([])
  const [followers, setFollowers] = useState(0)
  const [searchUser, setSearchUser] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

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

    // Remove from requests
    setRequests(prev => prev.filter(r => r.id !== id))

    // Fetch full user data
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

        {/* SEARCH + SEND */}
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
              <div key={index} className="friend-card">
                <h3>{f.username}</h3>
                <p>{f.bio || "No bio"}</p>

                <button 
                  className="remove-btn"
                  onClick={() => handleRemoveFriend(f.username)}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* RIGHT SIDE → NOTIFICATIONS */}
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