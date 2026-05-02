import React from 'react'
import AdminLobby from '../AdminLobby/Lobby'
import AdminLogs from '../AdminLogs/AdminLogs'

const AdminMainContent = ({activeTab}) => {
  switch (activeTab){
    case 'Pending_Logs':
        return <AdminLobby/>
    case 'All_Logs':
        return <AdminLogs/>
  }
}

export default AdminMainContent
