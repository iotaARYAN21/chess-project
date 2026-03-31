import React from 'react'
import './signup.css'
import { Link } from 'react-router-dom'
const SignUp = () => {
  return (
    <div className='signup'>
      <h1>4Chess</h1>
      <div className="s-details">
        <h2>Welcome Back</h2>
        <input type="text" id='name' placeholder='Name' />
        <input type="email" id='email' placeholder='Email'/>
        <input type="password" id='password' placeholder='Password' />
        <button >Signup</button>
        <p>Already have an account ? {" "} <Link to='/'>Log in</Link> </p>
      </div>
    </div>
  )
}

export default SignUp
