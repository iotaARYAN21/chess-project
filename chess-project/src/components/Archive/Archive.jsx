import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './archive.css';

const Archives = () => {
    const [matches, setMatches] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();
    const username = localStorage.getItem('username');

    useEffect(() => {
        fetch(`http://localhost:8000/users/${username}/matches`,{
        method: "GET",
        headers: {
          "Authorization": `Bearer ${localStorage.getItem('token')}`,
          "Content-Type": "application/json"
        }})
            .then(res => res.json())
            .then(data => {
                // Sort matches by ID descending to ensure the newest matches appear first
                console.log("data: ",data)
                const sortedMatches = data.sort((a, b) => b.id - a.id);
                setMatches(sortedMatches);
                console.log("sorted data: ",sortedMatches)
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to fetch matches:", err);
                setLoading(false);
            });
    }, [username]);

    if (loading) return <div className="archives-loading">Loading History...</div>;
    // console.log(matches[0].white_username)
    return (
        <div className="archives-container">
            <h2 className="archives-header">Match History</h2>
            <div className="archives-grid">
                {matches.map(match => (
                    <div 
                        key={match.id} 
                        className="match-card" 
                        onClick={() => navigate(`/replay/${match.id}`,{
                            state:{white:match.white_username,black:match.black_username}
                        })}
                    >
                        <div className="match-tag">{match.game_mode_name}</div>
                        <div className="match-players">
                            <span>{match.white_username}</span>
                            <span className="vs">vs</span>
                            <span>{match.black_username}</span>
                        </div>
                        <div className={`match-result ${match.result.toLowerCase()}`}>
                            {`${match.result==='draw' ? "Draw" : match.result==='white'?`Winner: ${match.white_username}` : `Winner: ${match.black_username}`}`}
                        </div>
                    </div>
                ))}
            </div>
            {matches.length === 0 && <p className="no-matches">No matches found in your archives.</p>}
        </div>
    );
};

export default Archives;