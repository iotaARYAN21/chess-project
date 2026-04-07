import React, { useState } from 'react'
import './lobby.css'
import { useNavigate } from 'react-router-dom';
function GameMode({id,title,subtitle,time,icon , onClick}){
    return <div className="game-card" onClick={onClick} style={{cursor:'pointer'}}>
        <h2>{id}</h2>
        <h3>{title}</h3>
        <p>{subtitle}</p>
        <p>{time} </p>
        <p> {icon} </p>
    </div>
}
const Lobby = () => {
    const [loading,setLoading]= useState(false);
    const navigate = useNavigate();
    const gameModes = [
    { id: 'bullet', title: 'Bullet', subtitle: 'Speed is everything.', time: '1 + 0', icon: '⚡' },
    { id: 'blitz', title: 'Blitz', subtitle: 'The expert standard.', time: '3 + 2', icon: '⏱️' },
    { id: 'rapid', title: 'Rapid', subtitle: 'Precision & logic.', time: '10 + 0', icon: '🕒' },
    ];
    const handleGameMode = async(game_id,game_time)=>{
        setLoading(true);
        try{
            const response = await fetch('http://localhost:8000/api/game/start',{
                method:'POST',
                headers:{
                    'Content-Type' : 'application/json',
                },
                body:JSON.stringify({
                    game_mode:game_time,
                }),
            });
            if(!response.ok){
                throw new Error('Failed to start game');
            }
            const data = await response.json();
            if(data.game_id){
                navigate(`/game/${data.game_id}`);
            }
            else{
                console.error("Game not found");
            }
        }
        catch(err){
            console.error("Error starting the game: ",err);
            alert("Could not start the game , Please try again")
        }
        finally{
            setLoading(false);
        }
    }
  return (
    <div className="lobby">
        <div className="lobby-intro">
            <h1>Quick Pair</h1>
        <p>Choose your battlefield. Ratings updated in real-time.</p>
        </div>
        <div className="games">
            {gameModes.map((item)=>(
            <GameMode key={item.id} id={item.id} title={item.title} subtitle={item.subtitle} time={item.time} icon={item.icon} onClick={()=>handleGameMode(item.id,item.time)} />
        ))}
        </div>
    </div>
  )
}

export default Lobby
