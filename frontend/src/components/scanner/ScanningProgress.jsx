import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { FiActivity, FiCheck, FiCircle } from 'react-icons/fi';

const STEPS = [
  { id: 'init', label: 'Initializing' },
  { id: 'parsing', label: 'Header & Body Parsing' },
  { id: 'heuristics', label: 'Heuristics & Auth' },
  { id: 'threat_intel', label: 'Threat Intel Lookup' },
  { id: 'ml_prediction', label: 'ML Prediction' },
  { id: 'xai', label: 'XAI Generation' },
  { id: 'done', label: 'Completed' }
];

const ScanningProgress = ({ status, currentStep, logs }) => {
  const terminalRef = useRef(null);

  // Auto-scroll terminal to bottom
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  const getCurrentStepIndex = () => {
    return STEPS.findIndex(s => s.id === currentStep);
  };

  const currentIndex = getCurrentStepIndex();

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 font-sans">
      {/* Stepper Component */}
      <motion.div 
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="glass-panel p-8 flex flex-col"
      >
        <h3 className="text-xl font-semibold mb-8 text-white border-b border-white/10 pb-4 flex items-center gap-2">
            <FiActivity className="text-primary" />
            Analysis Pipeline
        </h3>
        <div className="space-y-8 flex-1">
          {STEPS.map((step, index) => {
            const isCompleted = index < currentIndex || currentStep === 'done';
            const isActive = index === currentIndex && status !== 'failed';
            const isPending = index > currentIndex;

            let textColor = "text-gray-500";
            if (isCompleted) textColor = "text-primary font-medium";
            if (isActive) textColor = "text-secondary font-semibold";
            if (status === 'failed' && isActive) textColor = "text-danger font-semibold";

            return (
              <div key={step.id} className="flex items-center gap-6 relative">
                {/* Connecting Line */}
                {index < STEPS.length - 1 && (
                  <div className={`absolute top-8 left-3.5 -ml-px w-0.5 h-full ${isCompleted ? 'bg-primary/50' : 'bg-gray-700/50'}`} />
                )}
                
                <div className={`relative flex items-center justify-center w-7 h-7 rounded-full z-10 ${isCompleted ? 'bg-primary/20 text-primary border border-primary/50' : isActive ? 'bg-secondary/20 text-secondary border border-secondary/50 animate-pulse' : 'bg-gray-800 border border-gray-600 text-gray-500'}`}>
                  {isCompleted ? (
                    <FiCheck className="text-sm" />
                  ) : isActive ? (
                    <FiCircle className="text-sm animate-spin" />
                  ) : (
                    <div className="w-1.5 h-1.5 rounded-full bg-gray-500" />
                  )}
                </div>
                
                <div className={`text-sm ${textColor}`}>
                  {step.label}
                </div>
              </div>
            );
          })}
        </div>
      </motion.div>

      {/* Live Logs */}
      <motion.div 
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        className="glass-panel flex flex-col overflow-hidden"
      >
        <div className="bg-white/5 p-4 border-b border-white/10 flex items-center justify-between text-white font-medium">
          <span className="flex items-center gap-2"><FiActivity className="text-secondary" /> System Logs</span>
          {status === 'processing' && <span className="text-xs text-secondary animate-pulse px-2 py-1 bg-secondary/10 rounded-full border border-secondary/20">Live</span>}
        </div>
        <div 
          ref={terminalRef}
          className="bg-black/20 p-6 h-[450px] overflow-y-auto font-mono text-sm space-y-3 relative rounded-b-2xl scrollbar-hide"
        >
          {logs.map((log, i) => {
            let color = 'text-gray-300';
            
            if (log.includes('[ERROR]') || log.includes('WARNING')) {
                color = 'text-danger font-semibold';
            } else if (log.includes('System:')) {
                color = 'text-secondary';
            } else if (log.includes('[AI Model]') || log.includes('[XAI Engine]')) {
                color = 'text-primary';
            } else if (log.includes('[Threat Intel]')) {
                color = 'text-warning';
            }

            return (
                <motion.div 
                key={i}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className={`${color} flex gap-3 leading-relaxed`}
                >
                <span className="text-gray-600 select-none">{String(i+1).padStart(3, '0')}</span> 
                <span className="break-words flex-1">{log}</span>
                </motion.div>
            );
          })}
          {status === 'processing' && (
            <div className="flex gap-3 text-gray-500 mt-2">
              <span className="text-gray-600 select-none">{String(logs.length + 1).padStart(3, '0')}</span>
              <span className="animate-pulse">_</span>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
};

export default ScanningProgress;
