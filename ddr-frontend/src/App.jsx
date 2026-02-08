import "./App.css"

import * as THREE from "three"

import { Canvas, useLoader } from "@react-three/fiber"
import { useEffect, useRef, useState } from "react"

import { Stats } from "@react-three/drei"

function Arrow({ lane, position }) {
  const arrows = ['left-arrow.gif', 'down-arrow.gif', 'up-arrow.gif', 'right-arrow.gif']
  const texture = useLoader(THREE.TextureLoader, `/${arrows[lane]}`)
  
  return (
    <mesh position={position}>
      <planeGeometry args={[0.8, 0.8]} />
      <meshBasicMaterial map={texture} transparent />
    </mesh>
  )
}

function App() {
  const [notes, setNotes] = useState([])
  const [time, setTime] = useState(0)
  const [started, setStarted] = useState(false)
  const audioRef = useRef(null)
  const startTimeRef = useRef(null)

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws')
    
    ws.onopen = () => {
      console.log('Connected to game server')
    }
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'pose_update') {
        // Process joint data for lane detection
        const joints = data.joints
        console.log('Ankle positions:', joints.left_ankle, joints.right_ankle)
        // TODO: Map ankle X positions to lanes and trigger hits
      }
    }
    
    return () => ws.close()
  }, [])

  useEffect(() => {
    audioRef.current = new Audio('/output.ogg')
    audioRef.current.preload = 'auto'
  }, [])

  useEffect(() => {
    fetch('http://localhost:8000/api/beatmap')
      .then(res => res.json())
      .then(data => setNotes(data.notes))
  }, [])

  useEffect(() => {
    if (!started) return
    
    const timer = setInterval(() => {
      setTime((performance.now() - startTimeRef.current) / 1000)
    }, 16)
    
    return () => clearInterval(timer)
  }, [started])

  const handleStart = () => {
    if (started) return
    setStarted(true)
    startTimeRef.current = performance.now()
    audioRef.current.play().catch(e => console.error('Audio play failed:', e))
  }

  return (
    <>
      {!started && (
        <div onClick={handleStart} style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'rgba(0,0,0,0.8)',
          color: 'white',
          fontSize: '2rem',
          cursor: 'pointer',
          zIndex: 1000
        }}>
          Click to Start
        </div>
      )}
      <Canvas camera={{ position: [0, 0, 12], fov: 50 }}>
        <color attach="background" args={['#0a0a0a']} />
        <ambientLight />
        
        {notes.map((note, i) => {
          const x = (note.lane - 1.5) * 2
          const y = (note.time - time) * 5
          if (y < -5 || y > 15) return null
          return <Arrow key={i} lane={note.lane} position={[x, y, 0]} />
        })}
        
        {[0, 1, 2, 3].map(lane => (
          <Arrow key={lane} lane={lane} position={[(lane - 1.5) * 2, 0, 0]} />
        ))}
        
        <Stats />
      </Canvas>
    </>
  )
}

export default App