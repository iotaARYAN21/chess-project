import React, { useEffect, useState } from 'react'
import './friends.css'

const Friends = () => {

  const [friends, setFriends] = useState([])
  const [requests, setRequests] = useState([])
  const [followers, setFollowers] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const username = localStorage.getItem('username')

  useEffect(() => {
    if (!username) {
      setError("No user logged in")
      setLoading(false)
      return
    }

    async function fetchData() {
      try {
        // 🔹 Friends
        const fRes = await fetch("http://localhost:8000/social/friends")
        const fData = await fRes.json()

        if (fRes.ok) setFriends(fData)

        // 🔹 Friend Requests
        const rRes = await fetch("http://localhost:8000/social/friend-requests")
        const rData = await rRes.json()

        if (rRes.ok) setRequests(rData)

        // 🔹 Followers count (from profile)
        const pRes = await fetch(`http://localhost:8000/users/${username}`)
        const pData = await pRes.json()

        if (pRes.ok) setFollowers(pData.n_followers)

      } catch (err) {
        setError("Failed to load data")
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  // -------- ACTIONS --------

  const handleAccept = async (id) => {
    await fetch(`http://localhost:8000/social/friend-request/${id}/accept`, {
      method: "POST"
    })
    window.location.reload()
  }

  const handleDecline = async (id) => {
    await fetch(`http://localhost:8000/social/friend-request/${id}/decline`, {
      method: "POST"
    })
    window.location.reload()
  }

  if (loading) return <h2>Loading...</h2>
  if (error) return <h2 style={{color:'red'}}>{error}</h2>

  return (
    <div className="friends-container">

      {/* -------- FOLLOWERS -------- */}
      <div className="followers-box">
        <h2>Followers</h2>
        <p>{followers}</p>
      </div>

      {/* -------- FRIEND REQUESTS -------- */}
      <div className="requests-section">
        <h2>Pending Requests</h2>

        {requests.length === 0 && <p>No pending requests</p>}

        {requests.map((r) => (
          <div key={r.id} className="request-card">
            <span>{r.from_username}</span>

            <div className="actions">
              <button onClick={() => handleAccept(r.id)}>Accept</button>
              <button onClick={() => handleDecline(r.id)}>Decline</button>
            </div>
          </div>
        ))}
      </div>

      {/* -------- FRIENDS -------- */}
      <div className="friends-section">
        <h2>Your Friends</h2>

        {friends.length === 0 && <p>No friends yet</p>}

        <div className="friends-grid">
          {friends.map((f, index) => (
            <div key={index} className="friend-card">
              <h3>{f.username}</h3>
              <p>{f.bio || "No bio"}</p>
            </div>
          ))}
        </div>
      </div>

    </div>
  )
}

export default Friends