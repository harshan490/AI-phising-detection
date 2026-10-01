import React, { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { FiUser, FiSettings, FiLogOut } from 'react-icons/fi';
import { motion } from 'framer-motion';

const SettingsPage = () => {
  const { user, logout } = useContext(AuthContext);
  

  return (
    <div className="max-w-5xl mx-auto space-y-8 font-sans pb-20 pt-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2 text-white">System Settings</h1>
        <p className="text-gray-400 font-medium">Manage your account preferences and security configurations.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Navigation/Profile Summary */}
        <div className="space-y-6">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="glass-panel p-8 flex flex-col items-center text-center relative overflow-hidden"
          >
            <div className="absolute top-0 w-full h-24 bg-gradient-to-r from-primary/20 to-secondary/20"></div>
            <div className="w-24 h-24 rounded-full bg-white/10 backdrop-blur-md border-4 border-white/10 flex items-center justify-center text-white text-4xl mb-4 relative z-10 shadow-xl">
              <FiUser />
            </div>
            <h2 className="text-xl font-bold text-white z-10">{user?.full_name || user?.email}</h2>
            <p className="text-gray-400 text-sm mb-4 z-10">{user?.email}</p>
            <span className="px-4 py-1 bg-white/10 text-white rounded-full text-xs font-semibold border border-white/20 z-10">
              {user?.role || 'Analyst'}
            </span>
          </motion.div>
          
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="glass-panel overflow-hidden"
          >
            <div className="p-4 bg-white/10 border-l-4 border-primary text-white flex items-center gap-3 cursor-pointer text-sm font-semibold">
              <FiSettings className="text-primary" /> <span>Account</span>
            </div>
            <div 
              className="p-4 hover:bg-danger/10 flex items-center gap-3 cursor-pointer text-danger transition-colors border-t border-white/5 text-sm font-medium"
              onClick={logout}
            >
              <FiLogOut /> <span>Sign Out</span>
            </div>
          </motion.div>
        </div>

        {/* Right Column: Settings Content */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Profile Details */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass-panel p-8"
          >
            <h3 className="text-lg font-semibold mb-6 flex items-center gap-2 border-b border-white/10 pb-4 text-white">
              <FiUser className="text-secondary" /> Account Details
            </h3>
            
            <form className="space-y-6" onSubmit={(e) => e.preventDefault()}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Full Name</label>
                  <input 
                    type="text" 
                    className="w-full bg-black/20 border border-white/5 rounded-xl px-4 py-3 text-gray-300 cursor-not-allowed"
                    defaultValue={user?.full_name || ''}
                    disabled
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Email Address</label>
                  <input 
                    type="email" 
                    className="w-full bg-black/20 border border-white/5 rounded-xl px-4 py-3 text-gray-500 cursor-not-allowed"
                    defaultValue={user?.email || ''}
                    disabled
                  />
                </div>
              </div>
            </form>
          </motion.div>

        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
