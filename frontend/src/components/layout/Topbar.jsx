import React, { useContext } from 'react';
import { NavLink } from 'react-router-dom';
import { FiUser, FiShield } from 'react-icons/fi';
import { AuthContext } from '../../context/AuthContext';
import { motion } from 'framer-motion';

const Topbar = () => {
  const { user } = useContext(AuthContext);

  const navItems = [
    { name: 'Dashboard', path: '/' },
    { name: 'Scanning', path: '/scanner' },
    { name: 'Analytics', path: '/analytics' },
    { name: 'Settings', path: '/settings' }
  ];

  return (
    <motion.div 
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full flex justify-center pt-6 px-4 z-50 relative"
    >
      <div className="w-full max-w-6xl glass-panel px-6 py-4 flex items-center justify-between rounded-full">
          <div className="flex items-center gap-3 text-white font-bold text-xl tracking-wide">
            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-primary to-secondary flex items-center justify-center shadow-lg">
                <FiShield className="text-xl text-white" />
            </div>
            <span className="text-gradient">PhishSentinel</span>
          </div>

          <nav className="hidden md:flex items-center gap-1 bg-white/5 rounded-full p-1 border border-white/10">
            {navItems.map((item) => (
              <NavLink
                key={item.name}
                to={item.path}
                className={({ isActive }) =>
                  `px-5 py-2 rounded-full transition-all duration-300 font-medium text-sm ${
                    isActive
                      ? 'bg-white/10 text-white shadow-sm border border-white/10'
                      : 'bg-transparent text-white/60 border-transparent hover:text-white hover:bg-white/5'
                  }`
                }
              >
                {item.name}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-semibold text-white leading-tight">{user?.full_name || 'Admin User'}</p>
              <p className="text-xs text-primary/80">{user?.role || 'Analyst'}</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-white/10 border border-white/20 flex items-center justify-center text-white/80 hover:bg-white/20 transition-colors cursor-pointer shadow-sm">
              <FiUser className="text-lg" />
            </div>
          </div>
      </div>
    </motion.div>
  );
};

export default Topbar;
