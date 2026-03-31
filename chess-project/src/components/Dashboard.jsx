import React, { useState } from 'react'
import Sidebar from './Sidebar';
import MainContent from './MainContent';
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
