import React, { useState } from 'react'
import './login.css'
import Dashboard from '../Dashboard/Dashboard'
import { Link,useNavigate } from 'react-router-dom'
const Login = () => {

  const navigate = useNavigate();
  const [email,setEmail] = useState('');
  const [name,setName] = useState('');
  const [pwd,setPwd] = useState('');
  const [error,setError] = useState('');
  async function handleLogin(){
    console.log(email);
    console.log(name);
    console.log(pwd);
    try{
      const resp = await fetch('http://localhost:8000/auth/login',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({name,email,pwd}),
      })
      const data = await resp.json();
      console.log('response from backend: ',data);

      if(!resp.ok){
        setError(data.detail || 'Login failed');
        return;
      }

      localStorage.setItem('token',data.access_token)
      localStorage.setItem('username', name) 
      localStorage.setItem('userId',data.user_id)
      navigate('/dashboard')
    }catch(err){
      setError(err)
    }
  }
  return (
    <div className='login'>
      <h1>4Chess</h1>
      <div className="l-details">
        <h2>Welcome Back</h2>
        <input 
        type="text" 
        id='name' 
        placeholder='Name'
        onChange={(e)=>setName(e.target.value)}
        />
        <input 
        type="email" 
        id='email' 
        placeholder='Email'
        onChange={(e)=>setEmail(e.target.value)}
        />
        <input 
        type="password" 
        id='password' 
        placeholder='Password'
        onChange={e=>setPwd(e.target.value)}
        />
        <button onClick={handleLogin}>Login</button>
        {error && <p style={{color: 'red'}}>{error}</p>}
        <p>Don't have an account ? {" "}<Link to={"/signup"}>Sign up</Link> </p>
      </div>
    </div>
  )
}

export default Login
