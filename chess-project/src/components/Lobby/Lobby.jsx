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

// NOTE: CREATION OF GAME MUST BE HANDLED HERE
const Lobby = () => {
    const [loading,setLoading] = useState(false);
    const [botUsername,setBotUsername] = useState('stockfish_16')
    const navigate = useNavigate()
    const gameModes = [
    { id: 'bullet', title: 'Bullet', subtitle: 'Speed is everything.', time: '1 + 0', icon: '⚡' },
    { id: 'blitz', title: 'Blitz', subtitle: 'The expert standard.', time: '3 + 2', icon: '⏱️' },
    { id: 'rapid', title: 'Rapid', subtitle: 'Precision & logic.', time: '10 + 0', icon: '🕒' },
    {id: 'classical', title: 'Classical', subtitle: 'Deep strategy, no rush.', time: '30 + 0', icon: '♟️' },
];
    const handleGameMode = async (game_id,game_time)=>{
        setLoading(true);
        // console.log('fdfds')
        try{
            /*
            Creates a new game record against the selected bot in the database. 
            Initializes the starting FEN, sets clocks, and returns a game_id.
           */
           const userId = localStorage.getItem('userId');
           if(!userId){
                throw new Error('Please log in again to start a game')
           }
           const response = await fetch('http://localhost:8000/api/seek',{
            method:'POST',
            headers:{
                'Content-Type':'application/json',
                'Authorization':`Bearer ${localStorage.getItem('token')}`
            },
            body:JSON.stringify({
                game_mode: game_id,
                bot_username:botUsername,
                userid:userId
            })
           });
           if(!response.ok){
                let errorMessage = 'Failed to start a game';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorMessage;
                } catch(e) {
                    console.log("response not good")
                }
                throw new Error(errorMessage)
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
            console.error("Error starting the game: ", e);
            alert(e.message || "Could not start the game, Please try again");
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
        <div className="bot-selector" style={{ margin: '20px 0' , display:'flex', alignItems:'center'}}>
                    <label style={{ marginRight: '10px', fontWeight: 'bold' }}>Select Opponent: </label>
                    <select 
                        value={botUsername} 
                        onChange={(e) => setBotUsername(e.target.value)}
                        style={{ padding: '8px', borderRadius: '5px', cursor: 'pointer' }}
                        disabled={loading} // Prevent changing bot while fetching
                    >
                        <option value="stockfish_16">stockfish_16</option>
                        <option value="komodo_14">komodo_14</option>
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
