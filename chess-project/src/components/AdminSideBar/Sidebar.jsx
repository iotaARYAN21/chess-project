import React from 'react'
import './sidebar.css'
const Sidebar = ({activeTab,setActiveTab}) => {
  const navItems= [
    { id: 'lobby', label: 'Lobby', icon: 'grid-icon' },
    ];
    return (
        <div className="sidebar">
            <div className="side-profile">
                <h2>Profile Picture</h2>
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
