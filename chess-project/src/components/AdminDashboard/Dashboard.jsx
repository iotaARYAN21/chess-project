import React, { useState } from "react";
import Sidebar from "../AdminSideBar/Sidebar";
import AdminMainContent from "../AdminMainContent/MainContent";
import "./dashboard.css";
const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState("lobby");
  return (
    <div className="dash-container">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <div className="admin-main-screen">
        <AdminMainContent activeTab={activeTab} />
      </div>
    </div>
  );
};

export default AdminDashboard;
