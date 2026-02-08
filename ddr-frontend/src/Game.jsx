// Game.jsx - Minimal scrolling notes

import { useEffect, useState } from 'react'

const LANE_X = [-3, -1, 1, 3]
const COLORS = ['#ff0066', '#00ffff', '#ffff00', '#00ff66']

function Game() {
  const [notes, setNotes] = useState([])
  const [scroll, setScroll] = useState(0)
  
  useEffect(() => {
    fetch('http://localhost:8000/api/beatmap')
      .then(res => res.json())
      .then(data => setNotes(data.notes))
  }, [])
  
  useEffect(() => {
    const interval = setInterval(() => setScroll(s => s + 0.016), 16)
    return () => clearInterval(interval)
  }, [])
  
  return (
    <>
      <color attach="background" args={['#000']} />
      <ambientLight />
      
      {notes.map((note, i) => {
        const y = note.time - scroll
        if (y < -2 || y > 15) return null
        
        return (
          <mesh key={i} position={[LANE_X[note.lane], 0, -y * 2]}>
            <boxGeometry args={[0.8, 0.3, 0.3]} />
            <meshBasicMaterial color={COLORS[note.lane]} />
          </mesh>
        )
      })}
      
      {/* Hit line */}
      {[0,1,2,3].map(i => (
        <mesh key={i} position={[LANE_X[i], 0, 0]}>
          <boxGeometry args={[1, 0.1, 0.1]} />
          <meshBasicMaterial color="#fff" />
        </mesh>
      ))}
    </>
  )
}

export default Game