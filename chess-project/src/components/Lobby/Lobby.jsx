import React, { useState } from 'react'
import './lobby.css'
import { useNavigate } from 'react-router-dom';
function GameMode({id,title,subtitle,time,icon,onClick}){
    return <div className="game-card"  style={{cursor:'pointer'}} onClick={onClick}>
        <h2>{id}</h2>
        <h3>{title}</h3>
        <p>{subtitle}</p>
        <p>{time} </p>
        <p> {icon} </p>
    </div>
}
const Lobby = () => {
    const [loading,setLoading] = useState(false);
    const [botUsername,setBotUsername] = useState('Martin_Bot')
    const navigate = useNavigate()
    const gameModes = [
    { id: 'bullet', title: 'Bullet', subtitle: 'Speed is everything.', time: '1 + 0 min', icon: '⏱️' },
    { id: 'blitz', title: 'Blitz', subtitle: 'The expert standard.', time: '3 + 2 min', icon: '⏱️' },
    { id: 'rapid', title: 'Rapid', subtitle: 'Precision & logic.', time: '10 + 0 min', icon: '⏱️' },
    ];
    const handleGameMode = async (game_id,game_time)=>{
        setLoading(true);
        // console.log('fdfds')
        try{
            /*
            Creates a new game record against the selected bot in the database. 
            Initializes the starting FEN, sets clocks, and returns a game_id.
            */
           const response = await fetch('http://localhost:8000/seek',{
            method:'POST',
            headers:{
                'Content-Type':'application/json',
            },
            body:JSON.stringify({
                game_mode: game_time,
                bot_username:botUsername
            })
           });
           if(!response.ok){
                throw new Error('failed to start a game')
           }
           const data =  await response.json();
           if(data.game_id){
            // game_id is used to connect the frontend websocket with the server
                // We also pass the bot details so the GameBoard can display them
            navigate(`/game/${data.game_id}`,{
                state:{
                    opponentName: data.opponent_name || botUsername,
                    opponentId : data.opponent_id
                }
            });
           }
           else{
            console.log('game not found');
           }
        }
        catch(e){
            console.error("Error starting the game: ", err);
            alert("Could not start the game, Please try again");
        }
        finally {
            // console.log('fasfds')
            setLoading(false);
        }
    }
  return (
    <div className="lobby">
        <div className="lobby-intro">
            <h1>Quick Pair</h1>
        <p>Choose your battlefield. Ratings updated in real-time.</p>
        <div className="bot-selector" style={{ margin: '20px 0' }}>
                    <label style={{ marginRight: '10px', fontWeight: 'bold' }}>Select Opponent: </label>
                    <select 
                        value={botUsername} 
                        onChange={(e) => setBotUsername(e.target.value)}
                        style={{ padding: '8px', borderRadius: '5px', cursor: 'pointer' }}
                        disabled={loading} // Prevent changing bot while fetching
                    >
                        <option value="Martin_Bot">Martin (Beginner)</option>
                        <option value="Antonio_Bot">Antonio (Intermediate)</option>
                        <option value="GM_Magnus90">GM Magnus (Advanced)</option>
                    </select>
                </div>
        </div>
        <div className="games">
            {gameModes.map((item)=>(
            <GameMode 
            key={item.id} 
            id={item.id} 
            title={item.title} 
            subtitle={item.subtitle} 
            time={item.time} 
            icon={item.icon}
            onClick={()=>handleGameMode(item.id,item.time)}
            />
        ))}
        </div>
    </div>
  )
}

export default Lobby
