import React, { useState } from "react";
import Sidebar from "../AdminSideBar/Sidebar";
import MainContent from "../MainContent/MainContent";
import "./dashboard.css";
const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState("lobby");
  return (
    <div className="dash-container">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* <div className="main-screen">
        <MainContent activeTab={activeTab}/>
      </div> */}
    </div>
  );
};

export default AdminDashboard;
