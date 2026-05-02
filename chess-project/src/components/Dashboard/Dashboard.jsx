import React, { useState } from 'react'
import { useLocation } from 'react-router-dom';
import Sidebar from '../Sidebar/Sidebar';
import MainContent from '../MainContent/MainContent';
import './dashboard.css'
const Dashboard = () => {
  const location = useLocation();
  const initialTab =location.state?.activeTab || 'lobby';
  const [activeTab,setActiveTab] = useState(initialTab);
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
