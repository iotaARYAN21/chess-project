import React from 'react'
import Login from './components/Login'
import {Routes,Route} from 'react-router-dom'
import SignUp from './components/SignUp'
import Dashboard from './components/Dashboard'
import Lobby from './components/Lobby'
// import Profile
const App = () => {
  return (
    // <Routes>
    //   <Route path='/' element={<Login/>}></Route>
    //   <Route path='/signup' element={<SignUp/>}/>
    // </Routes>
    <Dashboard/>
    // <Lobby/>
  )
}

export default App
