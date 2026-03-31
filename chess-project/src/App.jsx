import React from 'react'
import Login from './components/Login'
import {Routes,Route} from 'react-router-dom'
import SignUp from './components/SignUp'
import Dashboard from './components/Dashboard'
const App = () => {
  return (
    // <Routes>
    //   <Route path='/' element={<Login/>}></Route>
    //   <Route path='/signup' element={<SignUp/>}/>
    // </Routes>
    <Dashboard/>
  )
}

export default App
