import React, { useMemo, useState } from 'react';
import { Chess } from 'chess.js';
import { Chessboard } from 'react-chessboard';
import './gameboard.css';
const GameBoard = () => {
  const [game, setGame] = useState(() => new Chess());
/*

game_id, white_id (Player 1), black_id (Player 2),
 moves (the PGN or move array), time_control, and result.
*/

// NOTE: I NEED TO MAKE CHANGES MAINLY HERE
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

  return (
    <div className="game-layout">
      <div className="player-card top-player">
        <img src="/avatar2.png" alt="Black Player" />
        <div>
          <h4>GM_Magnus90</h4>
          <span className="elo">Rating: 2850</span>
        </div>
        <div className="timer">10:00</div>
      </div>

      <div className="board-container">
        <div className="board">
          <Chessboard options={boardOptions} />
        </div>
      </div>

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