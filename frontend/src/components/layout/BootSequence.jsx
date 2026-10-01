import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const BootSequence = ({ onComplete }) => {
  const [isDone, setIsDone] = useState(false);

  useEffect(() => {
    // Just a smooth glass fade in instead of terminal texts
    const timer = setTimeout(() => {
      setIsDone(true);
      setTimeout(onComplete, 800);
    }, 1500);

    return () => clearTimeout(timer);
  }, [onComplete]);

  return (
    <AnimatePresence>
      {!isDone && (
        <motion.div 
          initial={{ opacity: 1 }}
          exit={{ opacity: 0, filter: "blur(20px)" }}
          transition={{ duration: 0.8, ease: "easeInOut" }}
          className="fixed inset-0 z-50 flex flex-col justify-center items-center bg-background"
        >
          <motion.div 
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 1, ease: "easeOut" }}
            className="flex flex-col items-center"
          >
            <div className="w-24 h-24 rounded-3xl bg-white/5 backdrop-blur-xl border border-white/20 shadow-[0_0_40px_rgba(96,165,250,0.3)] flex items-center justify-center mb-6">
                <span className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-br from-primary to-secondary">PS</span>
            </div>
            <h1 className="text-2xl font-light tracking-[0.2em] text-white/80">PHISHSENTINEL</h1>
            <div className="mt-8 w-48 h-1 bg-white/10 rounded-full overflow-hidden">
                <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: "100%" }}
                    transition={{ duration: 1.2, ease: "easeInOut" }}
                    className="h-full bg-gradient-to-r from-primary to-secondary"
                />
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default BootSequence;
