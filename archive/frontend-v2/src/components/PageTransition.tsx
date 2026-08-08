import React from 'react';
import { motion } from 'motion/react';

interface PageTransitionProps {
  children: React.ReactNode;
}

export function PageTransition({ children }: PageTransitionProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15, filter: 'blur(10px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      exit={{ opacity: 0, y: -15, filter: 'blur(10px)' }}
      transition={{ 
        duration: 0.5, 
        ease: [0.23, 1, 0.32, 1], // Custom cubic bezier for a premium feel
        staggerChildren: 0.1
      }}
      className="w-full h-full"
    >
      {children}
    </motion.div>
  );
}
