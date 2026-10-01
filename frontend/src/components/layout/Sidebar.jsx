import React from 'react';
import { NavLink } from 'react-router-dom';
import { FiHome, FiShield, FiActivity, FiSettings } from 'react-icons/fi';
import { motion } from 'framer-motion';

const Sidebar = () => {
  const menuItems = [
    { name: 'Dashboard', icon: <FiHome />, path: '/' },
    { name: 'Email Scanner', icon: <FiShield />, path: '/scanner' },
    { name: 'Analytics', icon: <FiActivity />, path: '/analytics' },
    { name: 'Settings', icon: <FiSettings />, path: '/settings' },
  ];

  return (
    <motion.div 
      initial={{ x: -250 }}
      animate={{ x: 0 }}
      className="w-64 h-screen glass-panel rounded-none border-t-0 border-b-0 border-l-0 flex flex-col pt-8"
    >
      <div className="px-6 mb-10 flex items-center gap-3 text-primary font-bold text-lg tracking-wider">
        <FiShield className="text-3xl flex-shrink-0" />
        <span className="leading-tight">PhishSentinel AI</span>
      </div>

      <nav className="flex-1 px-4 space-y-2">
        {menuItems.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-300 ${
                isActive
                  ? 'bg-primary/20 text-primary border border-primary/30 shadow-[0_0_15px_rgba(0,246,255,0.2)]'
                  : 'text-gray-400 hover:bg-white/5 hover:text-white'
              }`
            }
          >
            <span className="text-xl">{item.icon}</span>
            <span className="font-medium">{item.name}</span>
          </NavLink>
        ))}
      </nav>
      
      <div className="p-6 text-sm text-gray-500 text-center border-t border-white/10">
        © 2026 SOC Platform
      </div>
    </motion.div>
  );
};

export default Sidebar;
