const HIT_Z = -2

function Lane({ index }) {
  const x = (index - 1.5) * 2
  return (
    <>
      <mesh position={[x, 0, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[1.8, 30]} />
        <meshBasicMaterial color="#222" opacity={0.5} transparent />
      </mesh>
      <mesh position={[x, 0.1, HIT_Z]}>
        <boxGeometry args={[1.8, 0.1, 0.3]} />
        <meshStandardMaterial color="#ffffff" emissive="#ffffff" emissiveIntensity={0.5} />
      </mesh>
    </>
  )
}

export default Lane;