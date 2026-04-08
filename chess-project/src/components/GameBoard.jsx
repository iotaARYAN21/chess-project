import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Chess } from 'chess.js';
import { Chessboard } from 'react-chessboard';
import './gameboard.css';
import { useParams } from 'react-router-dom';
const GameBoard = () => {
  const {gameId} = useParams();
  const [game, setGame] = useState(() => new Chess());
  const [playerColor,setPlayerColor] = useState('white');
  const [connected,setConnected] = useState(false);

  const [playerTime,setPlayerTime] = useState(600000);
  const [botTime,setBotTime] = useState(600000);

  const wsref = useRef(null);

  useEffect(()=>{
    const wsUrl = `ws://localhost:8000/ws/game/${gameId}`;
    const socket = new WebSocket(wsUrl);
    wsref.current(socket)

    socket.onopen = () =>{
      console.log('Connected to game server')
      setConnected(true)
    }
    socket.onmessage = (e) =>{
      const data = JSON.parse(e.data)

      // handling different types of messages from the server
      switch(data.type){
        case 'game-state': // new state of the board,timer sent by the server
          const newGame = new Chess(data.fen)
          setGame(newGame)
          setPlayerTime(data.player_time_ms)
          setBotTime(data.bot_time_ms)
          if(data.player_color)setPlayerColor(data.player_color);
          break;
        
        case 'error':
          alert(`${data.message}`)
          break;
        case 'game-over':
          alert(`Game Over: Result: ${data.result}`)
          break;
        default:
            console.log('unknown',data.type)
      }
    };
    socket.onclose = () => {
      console.log('Disconnected from server')
      setConnected(false)
    };
    return ()=>{
      if(socket.readyState === 1)socket.close()
    };

  },[gameId])

  useEffect(()=>{  // to visually update the timer so that it is shown continuously decreasing and when the server time is obtained then updating it with it
    if(!connected || game.isGameOver())return ;

    const isWhiteTurn = game.turn() === 'w';
    const isPlayerTurn = (isWhiteTurn && playerColor==='white') || (!isWhiteTurn && playerColor==='black');

    const ticker = setInterval(()=>{
      if(isPlayerTurn){
        setPlayerTime(prev=> Math.max(0,prev-100))
      }
      else{
        setBotTime(prev => Math.max(0,prev-100))
      }
    },100);
    return ()=>clearInterval(ticker)
  },[game,playerColor,connected])
  /*
game_id, white_id (Player 1), black_id (Player 2),
 moves (the PGN or move array), time_control, and result.
*/
  const boardOptions = useMemo(() => ({
    id: 'game-board',
    position: game.fen(),
    allowDragging: true,
    onPieceDrop: ({ sourceSquare, targetSquare }) => {
      console.log('DROP FIRED:', sourceSquare, targetSquare); 

      if (!targetSquare) return false;

      const gameCopy = new Chess(game.fen());
      try {
        const move = gameCopy.move({
          from: sourceSquare,
          to: targetSquare,
          promotion: 'q',
        });

        if (!move) {
          console.log('Move returned null - illegal move');
          return false;
        }

        setGame(gameCopy);

        if(wsref.current && wsref.current.readyState === WebSocket.OPEN){
          wsref.current.send(JSON.stringify({
            type:'make_move',
            move:move.lan
          }))
        }

        console.log('Current FEN (Board Position):', gameCopy.fen());
        console.log('Current PGN (Move History):', gameCopy.pgn());
        console.log('Is Checkmate?', gameCopy.isCheckmate());
        return true;
      } catch (e) {
        console.log('Move error:', e.message); 
        return false;
      }
    },
    boardStyle: {
      width: '400px',
    },
  }), [game]);

// Helper to format ms into MM:SS (and tenths of a second if under 10s)
const formatTime = (ms) => { // as modes like blitz or bullets on different sites shows 10th of a second when the timer goes below 10 sec
    if (ms <= 0) return "0:00.0";
    
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    
    // If less than 10 seconds, show tenths of a second
    if (minutes === 0 && seconds < 10) {
        const tenths = Math.floor((ms % 1000) / 100);
        return `${seconds}.${tenths}`;
    }

    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
};

  return (
    <div className="game-layout">
      <div className="player-card top-player">
        <img src="/avatar2.png" alt="Black Player" />
        <div>
          <h4>GM_Magnus90 (BOT)</h4>
          <span className="elo">Rating: 2850</span>
        </div>
        <div className="clock">{formatTime(botTime)}</div>
      </div>

      <div className="board-container">
        <div className="board">
          <Chessboard options={boardOptions} />
        </div>
      </div>

      <div className="player-card bottom-player">
        <img src="/your-avatar.png" alt="White Player" />
        <div>
          <h4>Player</h4>
          <span className="elo">Rating: 1500</span>
        </div>
        <div className="clock">{formatTime(playerTime)}</div>
      </div>
    </div>
  );
};

export default GameBoard;