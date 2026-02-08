import { Canvas, useFrame } from '@react-three/fiber'
import React, { useRef, useState } from 'react'

import { createRoot } from 'react-dom/client'

const NOTE_SPEED = 5

function Note({ lane, time, currentTime }) {
  const laneX = (lane - 1.5) * 2
  const z = (time - currentTime) * NOTE_SPEED - 10
  
  if (z < -15 || z > 20) return null
  
  const color = ['#ff0000', '#00ff00', '#0000ff', '#ffff00'][lane]
  
  return (
    <mesh position={[laneX, 0, z]}>
      <boxGeometry args={[1.5, 0.2, 0.5]} />
      <meshStandardMaterial color={color} />
    </mesh>
  )
}

export default Note;