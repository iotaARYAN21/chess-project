import React, { useState } from 'react';
import { Chess } from 'chess.js';
import { Chessboard } from 'react-chessboard';
// import './Game.css';
import './gameboard.css'

const GameBoard = () => {
  // 1. Initialize the chess logic engine
  const [game, setGame] = useState(new Chess());

  // 2. Function to handle when a user drags and drops a piece
  const onDrop = (sourceSquare, targetSquare) => {
    // Make a copy of the game state to mutate
    const gameCopy = new Chess(game.fen());

    try {
      // Attempt the move in the chess.js engine
      const move = gameCopy.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: 'q', // Default to queen promotion for simplicity
      });

      // If the move is invalid, chess.js throws an error or returns null
      if (move === null) return false;

      // If legal, update the state!
      setGame(gameCopy);
      
      // --- DATABASE SYNC LOGIC GOES HERE ---
      // Here you would send the new state to your FastAPI backend
      console.log("Current FEN (Board Position):", gameCopy.fen());
      console.log("Current PGN (Move History):", gameCopy.pgn());
      console.log("Is Checkmate?", gameCopy.isCheckmate());
      
      return true; // Tells react-chessboard to snap the piece to the new square

    } catch (e) {
      // Invalid move (e.g., moving a knight like a bishop)
      return false; 
    }
  };

  return (
    <div className="game-layout">
      
      {/* --- OPPONENT INFO (Fetched from your DB) --- */}
      <div className="player-card top-player">
        <img src="/avatar2.png" alt="Black Player" />
        <div>
          <h4>GM_Magnus90</h4>
          <span className="elo">Rating: 2850</span>
        </div>
        <div className="timer">10:00</div>
      </div>

      {/* --- THE CHESS BOARD --- */}
      <div className="board-container">
        <div className="board">
        <Chessboard 
          position={game.fen()} // The board reads the FEN from chess.js
          onPieceDrop={onDrop}  // Triggers when a piece is dropped
          // boardWidth={400}
        />
      </div>
      </div>

      {/* --- YOUR INFO (Fetched from your DB) --- */}
      <div className="player-card bottom-player">
        <img src="/your-avatar.png" alt="White Player" />
        <div>
          <h4>Aryan</h4>
          <span className="elo">Rating: 1500</span>
        </div>
        <div className="timer">10:00</div>
      </div>

    </div>
  );
};

export default GameBoard;