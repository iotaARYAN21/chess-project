import React, { useEffect, useState, useMemo } from 'react';
import { useParams,useNavigate } from 'react-router-dom';
import { Chess } from 'chess.js';
import { Chessboard } from 'react-chessboard';
import './replaymatch.css'
const START_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';

const ReplayMatch = () => {
    const { matchId } = useParams();
    const [positions, setPositions] = useState([START_FEN]);
    const [moveIndex, setMoveIndex] = useState(0);
    const navigate = useNavigate();
    useEffect(() => {
        // Fetch PGN for this specific match
        fetch(`http://localhost:8000/users/match/${matchId}/pgn`,{
        method: "GET",
        headers: {
          "Authorization": `Bearer ${localStorage.getItem('token')}`,
          "Content-Type": "application/json"
        }})
            .then(res => res.json())
            .then(data => {
                const chess = new Chess();
                // console.log(data.pgn);
                chess.loadPgn(data.pgn);
                const history = chess.history({ verbose: true });

                const replay = new Chess();
                const snaps = [replay.fen()];
                for (const move of history) {
                    replay.move(move);
                    snaps.push(replay.fen());
                }
                setPositions(snaps);
            });
    }, [matchId]);

    const boardOptions = useMemo(() => ({
        position: positions[moveIndex],
        allowDragging: false,
    }), [positions, moveIndex]);

    return (
        <div className="replay-div">
            <div style={{ width: '450px', margin: 'auto' }}>
            <Chessboard options={boardOptions} />
            <div className="controls">
                {/* <button onClick={() => setMoveIndex(0)}>⏮</button> */}
                <button onClick={() => setMoveIndex(m => Math.max(0, m - 1))}>◀</button>
                <button onClick={() => setMoveIndex(m => Math.min(positions.length - 1, m + 1))}>▶</button>
                {/* <button onClick={() => setMoveIndex(positions.length - 1)}>⏭</button> */}
            </div>
            <button id='back-btn' onClick={()=>navigate('/dashboard')}>Back</button>
        </div>
        </div>
    );
};

export default ReplayMatch;