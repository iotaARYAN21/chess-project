import React, { useEffect, useState, useMemo } from 'react';
import { useParams,useNavigate, useLocation } from 'react-router-dom';
import { Chess } from 'chess.js';
import { Chessboard } from 'react-chessboard';
import './replaymatch.css'
const START_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';

const ReplayMatch = () => {
    const { matchId } = useParams();
    const [positions, setPositions] = useState([START_FEN]);
    const [moveIndex, setMoveIndex] = useState(0);
    const navigate = useNavigate();
    const [moves,setMoves]=useState([])
    const location  = useLocation();
    // console.log(location)
    const {white,black}=location.state || {white:'White Player',black:"Black Player"}
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
                const historyText = chess.history();
                setMoves(historyText)

                const historyVerbose = chess.history({ verbose: true });

                const replay = new Chess();
                const snaps = [replay.fen()];
                for (const move of historyVerbose) {
                    replay.move(move);
                    snaps.push(replay.fen());
                }
                setPositions(snaps);
            });
    }, [matchId]);

    useEffect(()=>{
        const handleKeyDown = (event)=>{
            if(event.key === 'ArrowLeft'){
                setMoveIndex(m=>Math.max(0,m-1));
            }else if(event.key === 'ArrowRight'){
                setMoveIndex(m=>Math.min(positions.length-1,m+1))
            }
        }
        window.addEventListener('keydown',handleKeyDown)

        return ()=>{
            window.removeEventListener('keydown',handleKeyDown)
        }
    },[positions.length])

    const boardOptions = useMemo(() => ({
        position: positions[moveIndex],
        allowDragging: false,
    }), [positions, moveIndex]);

    const movePairs = [];
    for(let i=0;i<moves.length;i+=2){
        movePairs.push({
            white:moves[i],
            black:moves[i+1] ? moves[i+1]:'',
            whiteIndex:i+1,
            blackIndex:i+2
        })
    }
    return (
        <div className="replay-div">
            <button id='back-btn' onClick={()=>navigate('/dashboard',{
                state:{activeTab:'archives'}
            })}>← Back</button>
            <div className="board-column">
                <div className="player-tag black-player"> ♔ {black}</div>
                <div style={{ width: '500px', margin: 'auto' }}>
                <Chessboard options={boardOptions} />
                </div>
                <div className="player-tag white-player"> ♚ {white}</div>
                <div className="controls">
                    {/* <button onClick={() => setMoveIndex(0)}>⏮</button> */}
                    <button onClick={() => setMoveIndex(m => Math.max(0, m - 1))}>◀</button>
                    <button onClick={() => setMoveIndex(m => Math.min(positions.length - 1, m + 1))}>▶</button>
                    {/* <button onClick={() => setMoveIndex(positions.length - 1)}>⏭</button> */}
                </div>
                
            </div>
            <div className="pgn-column">
                <h3>Match History</h3>
                <div className="moves-container">
                    {movePairs.map((pair, idx) => (
                        <div key={idx} className="move-row">
                            <span className="move-number">{idx + 1}.</span>
                            
                            {/* White Move */}
                            <span 
                                className={`move ${moveIndex === pair.whiteIndex ? 'active' : ''}`} 
                                onClick={() => setMoveIndex(pair.whiteIndex)}
                            >
                                {pair.white}
                            </span>
                            
                            {/* Black Move */}
                            {pair.black ? (
                                <span 
                                    className={`move ${moveIndex === pair.blackIndex ? 'active' : ''}`} 
                                    onClick={() => setMoveIndex(pair.blackIndex)}
                                >
                                    {pair.black}
                                </span>
                            ) : (
                                <span className="move empty"></span>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default ReplayMatch;