import React from 'react';
import { motion } from 'framer-motion';

const StatCard = ({ title, value, icon, colorClass, delay = 0, footer }) => {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className={`glass-panel p-6 relative flex flex-col justify-between group overflow-hidden`}
    >
      {/* Background glow effect based on colorClass */}
      <div className={`absolute -right-6 -top-6 w-24 h-24 rounded-full blur-2xl opacity-20 transition-opacity group-hover:opacity-40 bg-current ${colorClass}`}></div>

      <div className="flex justify-between items-start mb-6 z-10">
        <h3 className="text-gray-400 font-medium text-sm">{title}</h3>
        <div className={`text-2xl ${colorClass} p-2 bg-white/5 rounded-xl border border-white/5`}>
          {icon}
        </div>
      </div>
      
      <div className={`text-4xl font-bold font-sans ${colorClass} z-10`}>
        {value}
      </div>
      {footer && (
        <div className="text-xs text-gray-500 mt-4 border-t border-white/10 pt-3 z-10">{footer}</div>
      )}
    </motion.div>
  );
};

export default StatCard;
