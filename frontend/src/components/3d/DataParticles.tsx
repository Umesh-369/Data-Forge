'use client';

import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

function ParticleField({ count = 800 }: { count?: number }) {
  const pointsRef = useRef<THREE.Points>(null!);

  const { positions, colors } = useMemo(() => {
    const pos = new Float32Array(count * 3);
    const col = new Float32Array(count * 3);

    const colorChoices = [
      new THREE.Color('#0284c7'), // Sky Blue Primary
      new THREE.Color('#0ea5e9'), // Vivid Sky Blue
      new THREE.Color('#38bdf8'), // Bright Sky Spark
      new THREE.Color('#d97706'), // Warm Amber Accent
    ];

    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 15;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 15;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 15;

      const c = colorChoices[Math.floor(Math.random() * colorChoices.length)];
      col[i * 3] = c.r;
      col[i * 3 + 1] = c.g;
      col[i * 3 + 2] = c.b;
    }

    return { positions: pos, colors: col };
  }, [count]);

  useFrame((state, delta) => {
    if (pointsRef.current) {
      pointsRef.current.rotation.y += delta * 0.05;
      pointsRef.current.rotation.x += delta * 0.02;
    }
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
        />
        <bufferAttribute
          attach="attributes-color"
          args={[colors, 3]}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.06}
        vertexColors
        transparent
        opacity={0.65}
      />
    </points>
  );
}

export default function DataParticlesCanvas({ active = true }: { active?: boolean }) {
  if (!active) return null; // Pauses and unmounts R3F canvas when inactive (Invariant I9 & Section 4.4)

  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden" style={{ pointerEvents: 'none' }}>
      <Canvas
        camera={{ position: [0, 0, 8], fov: 60 }}
        gl={{ antialias: true, alpha: true }}
        style={{ pointerEvents: 'none' }}
      >
        <ambientLight intensity={0.5} />
        <ParticleField count={1000} />
      </Canvas>
    </div>
  );
}
