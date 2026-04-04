import React from 'react'
import './friends.css'
const Friends = () => {
    const friends = [
        {id:'p1',rating:'3434',status:'accepted'},
        {id:'p2',rating:'3132',status:'pending'},
        {id:'p3',rating:"2323",status:'accepted'}
    ];
  return (
    <div className="friends-details">
            <h2>Friends</h2>
            {/* <p>fetch all the available friends and request pending in a list and map throught it and display</p> */}
            {friends.map((item)=>(
                <div key={item.id} className="friend">
                    {/* {item.id} {" "} {item.rating} {" "} {item.status}
                     */}
                     <h3>{item.id} </h3>
                     <h3> {item.rating} </h3>
                     <h3> {item.status} </h3>
                </div>
            ))}
        </div>
  )
}

export default Friends
