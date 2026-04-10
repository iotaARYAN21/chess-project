import React from 'react'
import Lobby from './Lobby'
import Profile from './Profile/Profile'
import Friends from './Friends'
function LobbyView(){
    return <div className='lobby'>
        <h1>Quick Pair</h1>
        <p>Choose your battlefield. Ratings updated in real-time.</p>
    </div>
}
function TournamentView(){
    return <div className="tournament">
        <h1>Tournaments</h1>
        <p>Upcoming matches</p>
    </div>
}
function FriendsView(){
    return <div className="friends">
        <h1>Friends</h1>
        <p>Manage your friends list...</p>
    </div>
}
function ArchivesView(){
    return <div className="archives">
        <h1>Archives</h1>
        <p>Check your archives here</p>
    </div>
}
const MainContent = ({activeTab}) => {
  switch (activeTab){
    case 'lobby':
        return <Lobby/>
    // case 'tournaments':
    //     return <TournamentView/>
    case 'friends':
        return <Friends/>
    case 'archives':
        return <ArchivesView/>
    case 'profile':
        return <Profile/>
  }
}

export default MainContent
