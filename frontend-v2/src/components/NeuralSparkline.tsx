import React, { useEffect, useState, useRef } from 'react';
import { motion } from 'motion/react';

export function NeuralSparkline({ color = '#6366f1' }: { color?: string }) {
  const [points, setPoints] = useState<number[]>(Array(20).fill(20));
  const requestRef = useRef<number>(0);

  useEffect(() => {
    const update = () => {
      setPoints(prev => {
        const next = [...prev.slice(1), Math.random() * 30 + 10];
        return next;
      });
      requestRef.current = requestAnimationFrame(update);
    };

    const interval = setInterval(() => {
      // Just to slow it down for better performance if needed, 
      // but let's try a slower interval instead of RAF for this simple decoration
    }, 200);

    const slowUpdate = () => {
        setPoints(prev => {
            const next = [...prev.slice(1), Math.random() * 30 + 10];
            return next;
        });
    }
    const timer = setInterval(slowUpdate, 400);

    return () => clearInterval(timer);
  }, []);

  const path = points.map((p, i) => `${i * 10},${50 - p}`).join(' L ');

  return (
    <svg width="200" height="50" className="opacity-40">
       <motion.path
         d={`M 0,${50 - points[0]} L ${path}`}
         fill="none"
         stroke={color}
         strokeWidth="2"
         strokeLinecap="round"
         initial={false}
         animate={{ d: `M 0,${50 - points[0]} L ${path}` }}
         transition={{ duration: 0.4, ease: "linear" }}
       />
    </svg>
  );
}
