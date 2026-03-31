import React from 'react'
import './login.css'
import { Link } from 'react-router-dom'
const Login = () => {
  return (
    <div className='login'>
      <h1>4Chess</h1>
      <div className="l-details">
        <h2>Welcome Back</h2>
        <input type="text" id='name' placeholder='Name' />
        <input type="email" id='email' placeholder='Email'/>
        <input type="password" id='password' placeholder='Password' />
        <button>Login</button>
        <p>Don't have an account ? {" "}<Link to={"/signup"}>Sign up</Link> </p>
      </div>
    </div>
  )
}

export default Login
