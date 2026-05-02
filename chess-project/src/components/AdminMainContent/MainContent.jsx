import React from 'react'
import AdminLobby from '../AdminLobby/Lobby'

const AdminMainContent = ({activeTab}) => {
  switch (activeTab){
    case 'lobby':
        return <AdminLobby/>
  }
}

export default AdminMainContent
