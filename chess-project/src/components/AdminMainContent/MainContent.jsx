import React from 'react'
import AdminLobby from '../AdminLobby/Lobby'
import AdminLogs from '../AdminLogs/AdminLogs'
import AdminBans from '../AdminBans/AdminBans'

const AdminMainContent = ({activeTab}) => {
  switch (activeTab){
    case 'Pending_Logs':
        return <AdminLobby/>
    case 'All_Logs':
        return <AdminLogs/>
    case 'All_Bans':
        return <AdminBans/>
  }
}

export default AdminMainContent
