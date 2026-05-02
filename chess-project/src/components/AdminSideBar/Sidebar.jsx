import React from 'react'
import './sidebar.css'
const Sidebar = ({activeTab,setActiveTab}) => {
  const navItems= [
    { id: 'Pending_Logs', label: 'Pending Logs', icon: 'grid-icon' },
    { id: 'All_Logs', label: 'All Logs', icon: 'grid-icon' },
    ];

    const username = localStorage.getItem('username');

    return (
        <div className="sidebar">
            <div className="side-profile">
                <h6>{username}</h6>
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
