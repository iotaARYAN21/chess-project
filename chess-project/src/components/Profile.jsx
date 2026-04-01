import React from 'react'
import './profile.css'
const Profile = () => {
    // const friends = [
    //     {id:'p1',rating:'3434',status:'accepted'},
    //     {id:'p2',rating:'3132',status:'pending'},
    //     {id:'03',rating:"2323",status:'accepted'}
    // ];
  return (
    <div className="profile-container">
        {/* image rating graph username , email bio, followers , friends,id */}
        <img src="" alt="Profile pic" className="profile-image" />
        <div className="rating-graph">Lorem ipsum dolor sit amet consectetur adipisicing elit. Fugiat beatae natus amet voluptatem repellendus velit sit laboriosam aperiam pariatur! Ut minima suscipit, at, velit aperiam distinctio architecto dignissimos dicta omnis aliquid delectus praesentium reprehenderit repudiandae ipsa repellendus voluptas iure commodi a. Eaque at ipsum dignissimos dicta cumque tempora atque quia!</div>
        
        <div className="player-info">
            <h2>id : 32</h2>
            <h2>Username : Simeon</h2>
            <h2>Rating : 4324</h2>
            <h2>Email : simeon@gmail.com</h2>
            <h2>Bio :  </h2>
            <h2>Followers :</h2>
            <h2>Following :</h2>
        </div>
        
    </div>
  )
}

export default Profile
