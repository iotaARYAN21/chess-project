import React from 'react'
import Login from './components/Login/Login'
import {Routes,Route, Navigate} from 'react-router-dom'
import SignUp from './components/SignUp/SignUp'
import Dashboard from './components/Dashboard/Dashboard'
import Lobby from './components/Lobby/Lobby'
import GameBoard from './components/GameBoard/GameBoard'
import Archive from './components/Archive/Archive'
import ReplayMatch from './components/ReplayMatch/ReplayMatch'
import AdminDashboard from './components/AdminDashboard/Dashboard'

// import Profile
function ProtectedRoute({children}){
  const token = localStorage.getItem('token');
  if(!token){
    return <Navigate to="/"/>
  }
  return children;
}
const App = () => {
  return (
    <Routes>
      <Route path='/' element={<Login/>}></Route>
      <Route path='/signup' element={<SignUp/>}/>
    
    <Route path='/dashboard' element={
      <ProtectedRoute>
        <Dashboard/>
      </ProtectedRoute>
    }>
    </Route>

    <Route path='/admin-dashboard' element={
      <ProtectedRoute>
        <AdminDashboard/>
      </ProtectedRoute>
    }></Route>

    <Route
    path='/lobby'
    element={
      <ProtectedRoute>
        <Lobby/>
      </ProtectedRoute>
    }
    ></Route>
    <Route
    path='/gameboard'
    element={
      <ProtectedRoute>
        <GameBoard/>
      </ProtectedRoute>
    }
    ></Route>
    <Route path='/replay/:matchId' element={
      <ProtectedRoute>
        <ReplayMatch/>
      </ProtectedRoute>
    }></Route>
    <Route path='/archive'
    element={
      <ProtectedRoute>
        <Archive/>
        </ProtectedRoute>
    }
    >
    </Route>
    </Routes>
  )
}

export default App
