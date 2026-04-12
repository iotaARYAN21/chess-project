import React from 'react'
import Login from './components/Login/Login'
import {Routes,Route, Navigate} from 'react-router-dom'
import SignUp from './components/SignUp/SignUp'
import Dashboard from './components/Dashboard/Dashboard'
import Lobby from './components/Lobby/Lobby'
import GameBoard from './components/GameBoard/GameBoard'
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
    </Routes>
  )
}

export default App
