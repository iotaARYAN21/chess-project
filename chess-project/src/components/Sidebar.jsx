import React from 'react'
import './sidebar.css'
const Sidebar = ({activeTab,setActiveTab}) => {
  const navItems= [
        { id: 'lobby', label: 'Lobby', icon: 'grid-icon' },
    // { id: 'tournaments', label: 'Tournaments', icon: 'trophy-icon' },
    { id: 'friends', label: 'Friends', icon: 'users-icon' },
    { id: 'archives', label: 'Archives', icon: 'history-icon' },
    {id:'profile',label:'Profile',icon:''}
    ];
    return (
        <div className="sidebar">
            <div className="side-profile">
                <h2>Options</h2>
            </div>
            <nav className='side-nav'>
                {navItems.map((item)=>(
                    <button key={item.id} className={`side-btn ${activeTab==item.id ? 'active':''}`} onClick={()=>{setActiveTab(item.id)}}>
                        {item.label}
                    </button>
                ))}
            </nav>
        </div>
    )
}

export default Sidebar
