import React from 'react'
import './lobby.css'
function GameMode({id,title,subtitle,time,icon}){
    return <div className="game-card" >
        <h2>{id}</h2>
        <h3>{title}</h3>
        <p>{subtitle}</p>
        <p>{time} </p>
        <p> {icon} </p>
    </div>
}
const Lobby = () => {
    const gameModes = [
    { id: 'bullet', title: 'Bullet', subtitle: 'Speed is everything.', time: '1 + 0', icon: '⚡' },
    { id: 'blitz', title: 'Blitz', subtitle: 'The expert standard.', time: '3 + 2', icon: '⏱️' },
    { id: 'rapid', title: 'Rapid', subtitle: 'Precision & logic.', time: '10 + 0', icon: '🕒' },
    ];
  return (
    <div className="lobby">
        <div className="lobby-intro">
            <h1>Quick Pair</h1>
        <p>Choose your battlefield. Ratings updated in real-time.</p>
        </div>
        <div className="games">
            {gameModes.map((item)=>(
            <GameMode key={item.id} id={item.id} title={item.title} subtitle={item.subtitle} time={item.time} icon={item.icon} />
        ))}
        </div>
    </div>
  )
}

export default Lobby
