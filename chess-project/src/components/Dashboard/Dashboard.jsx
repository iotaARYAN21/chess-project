import React, { useState } from 'react'
import Sidebar from '../Sidebar/Sidebar';
import MainContent from '../MainContent';
import './dashboard.css'
const Dashboard = () => {
    const [activeTab,setActiveTab] = useState('lobby');
  return (
    <div className='dash-container'>
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab}/>

      <div className="main-screen">
        <MainContent activeTab={activeTab}/>
      </div>
    </div>
  )
}

export default Dashboard
