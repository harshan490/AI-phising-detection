import React, { useEffect, useState } from 'react';
import { FiMail, FiShieldOff, FiCheckCircle, FiAlertTriangle, FiActivity, FiPieChart, FiList } from 'react-icons/fi';
import { getDashboard } from '../utils/api';
import StatCard from '../components/dashboard/StatCard';
import { motion } from 'framer-motion';

const DashboardPage = () => {
  const [stats, setStats] = useState(null);
  const [recentScans, setRecentScans] = useState([]);
  const [verdictCounts, setVerdictCounts] = useState({});
  const [error, setError] = useState(null);

  useEffect(() => {
    getDashboard()
      .then((d) => {
        setStats(d.stats);
        setRecentScans(d.recentScans);
        setVerdictCounts(d.verdictCounts);
      })
      .catch(() => setError('Could not load dashboard statistics.'));
  }, []);

  if (error) return <div className="glass-panel-danger p-6 mt-20 text-center text-danger">{error}</div>;

  const total = stats ? stats.totalScans : 0;
  const maliciousPct = total ? Math.round(((verdictCounts.Phishing || 0) / total) * 100) : null;
  const suspiciousPct = total ? Math.round(((verdictCounts.Suspicious || 0) / total) * 100) : 0;
  const safePct = total ? 100 - maliciousPct - suspiciousPct : 0;

  if (!stats) return (
    <div className="flex flex-col items-center justify-center mt-40">
        <FiActivity className="text-4xl text-primary animate-pulse mb-4" />
        <div className="text-white font-medium text-sm">Loading Intel...</div>
    </div>
  );

  return (
    <div className="space-y-8 pb-20 pt-8 max-w-6xl mx-auto font-sans">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2 text-white">Dashboard Overview</h1>
        <p className="text-gray-400">Real-time threat intelligence and system analytics.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Total Scans" 
          value={stats.totalScans} 
          icon={<FiMail />} 
          colorClass="text-primary"
          delay={0.1}
        />
        <StatCard 
          title="Phishing Detected" 
          value={stats.phishingCaught} 
          footer={`${stats.suspicious} more flagged suspicious`}
          icon={<FiShieldOff />} 
          colorClass="text-danger"
          delay={0.2}
        />
        <StatCard 
          title="Safe Emails" 
          value={stats.safeEmails} 
          icon={<FiCheckCircle />} 
          colorClass="text-secondary"
          delay={0.3}
        />
        <StatCard 
          title="System Threat Level" 
          value={stats.threatLevel} 
          icon={<FiAlertTriangle />} 
          colorClass="text-warning"
          delay={0.4}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="lg:col-span-2 glass-panel p-6 min-h-[400px] flex flex-col"
        >
          <div className="flex items-center gap-2 text-lg font-semibold text-white mb-6 border-b border-white/10 pb-4">
            <FiList className="text-secondary" /> Recent Scan Logs
          </div>
          
          <div className="space-y-3 flex-1">
            <div className="grid grid-cols-12 text-sm font-medium text-gray-400 pb-2 border-b border-white/5 mb-3 px-2">
                <div className="col-span-3">Status</div>
                <div className="col-span-6">Payload Subject</div>
                <div className="col-span-3 text-right">Timestamp</div>
            </div>
            {recentScans.length === 0 && (
              <p className="text-gray-500 text-sm px-2 py-6">No scans yet. Upload an .eml file in the scanner.</p>
            )}
            {recentScans.map((scan) => (
              <div key={scan.id} className="grid grid-cols-12 items-center px-2 py-3 bg-white/5 rounded-xl border border-white/5 hover:bg-white/10 transition-colors text-sm">
                  <div className="col-span-3">
                      {scan.status === 'Phishing' ? (
                          <span className="text-danger bg-danger/10 px-3 py-1 rounded-full text-xs font-semibold border border-danger/20">Phishing {Math.round(scan.risk)}</span>
                      ) : scan.status === 'Suspicious' ? (
                          <span className="text-warning bg-warning/10 px-3 py-1 rounded-full text-xs font-semibold border border-warning/20">Suspicious {Math.round(scan.risk)}</span>
                      ) : (
                          <span className="text-primary bg-primary/10 px-3 py-1 rounded-full text-xs font-semibold border border-primary/20">Safe {Math.round(scan.risk)}</span>
                      )}
                  </div>
                  <div className="col-span-6 truncate text-gray-200 pr-4">
                      {scan.subject}
                  </div>
                  <div className="col-span-3 text-right text-gray-500 text-xs">
                      {scan.date}
                  </div>
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="glass-panel p-6 flex flex-col"
        >
          <div className="flex items-center gap-2 text-lg font-semibold text-white mb-6 border-b border-white/10 pb-4">
            <FiPieChart className="text-primary" /> Threat Distribution
          </div>
          <div className="flex-1 flex flex-col items-center justify-center relative min-h-[300px]">
             {/* Modern Doughnut Chart UI */}
             <div className="relative w-48 h-48">
                 <div className="absolute inset-0 rounded-full" style={{
                   background: total
                     ? `conic-gradient(#fb7185 0 ${maliciousPct}%, #fbbf24 ${maliciousPct}% ${maliciousPct + suspiciousPct}%, #60a5fa ${maliciousPct + suspiciousPct}% 100%)`
                     : 'rgba(255,255,255,0.05)',
                 }}></div>
                 <div className="absolute inset-[12px] rounded-full bg-background"></div>
                 <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <p className="text-3xl font-bold text-white drop-shadow-md">{maliciousPct === null ? 'N/A' : `${maliciousPct}%`}</p>
                    <p className="text-xs text-gray-400 font-medium">Phishing</p>
                 </div>
             </div>

             <div className="mt-8 flex gap-6 w-full justify-center">
                 <div className="flex items-center gap-2">
                     <div className="w-3 h-3 rounded-full bg-primary shadow-[0_0_10px_rgba(96,165,250,0.5)]"></div>
                     <span className="text-sm text-gray-300">Safe {total ? `${safePct}%` : ''}</span>
                 </div>
                 <div className="flex items-center gap-2">
                     <div className="w-3 h-3 rounded-full bg-danger shadow-[0_0_10px_rgba(251,113,133,0.5)]"></div>
                     <span className="text-sm text-gray-300">Phishing</span>
                 </div>
                 <div className="flex items-center gap-2">
                     <div className="w-3 h-3 rounded-full bg-warning"></div>
                     <span className="text-sm text-gray-300">Suspicious {total ? `${suspiciousPct}%` : ''}</span>
                 </div>
             </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default DashboardPage;
