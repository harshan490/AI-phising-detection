import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { FiPieChart, FiTrendingUp, FiList, FiCpu, FiDatabase } from 'react-icons/fi';
import {
  Chart as ChartJS, ArcElement, BarElement, CategoryScale, LinearScale, LineElement, PointElement, Tooltip, Legend,
} from 'chart.js';
import { Doughnut, Line, Bar } from 'react-chartjs-2';
import { getDashboard, getModelMetrics, getIocs } from '../utils/api';

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, LineElement, PointElement, Tooltip, Legend);

const COLORS = { Safe: '#60a5fa', Suspicious: '#fbbf24', Phishing: '#fb7185' };
const axis = { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.06)' } };
const legend = { labels: { color: '#d1d5db' } };

const Panel = ({ icon, title, children, className = '', delay = 0 }) => (
  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay }}
    className={`glass-panel p-6 flex flex-col ${className}`}>
    <div className="flex items-center gap-2 text-lg font-semibold text-white mb-6 border-b border-white/10 pb-4">
      {icon} {title}
    </div>
    {children}
  </motion.div>
);

const Empty = ({ text = 'Not available' }) => <p className="text-gray-500 text-sm py-10 text-center">{text}</p>;

const pct = (v) => (v === undefined ? 'N/A' : `${(v * 100).toFixed(2)}%`);

const AnalyticsPage = () => {
  const [dash, setDash] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [iocs, setIocs] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    getDashboard().then(setDash).catch(() => setError('Could not load analytics.'));
    getModelMetrics().then(setMetrics).catch(() => setMetrics(false));
    getIocs().then(setIocs).catch(() => setIocs([]));
  }, []);

  if (error) return <div className="glass-panel-danger p-6 mt-20 text-center text-danger">{error}</div>;
  if (!dash) return <div className="text-gray-400 p-8 text-center mt-20">Loading analytics...</div>;

  const verdicts = ['Safe', 'Suspicious', 'Phishing'];
  const total = dash.stats.totalScans;
  const cm = metrics?.confusion_matrix?.matrix;

  return (
    <div className="space-y-6 pb-20 pt-8 max-w-6xl mx-auto font-sans">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2 text-white">Analytics</h1>
        <p className="text-gray-400">Computed from your stored scans and the trained model's evaluation.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Panel icon={<FiPieChart className="text-primary" />} title="Verdict Distribution" delay={0.1}>
          {total ? (
            <Doughnut
              data={{ labels: verdicts, datasets: [{ data: verdicts.map((v) => dash.verdictCounts[v] || 0), backgroundColor: verdicts.map((v) => COLORS[v]), borderWidth: 0 }] }}
              options={{ plugins: { legend }, cutout: '70%' }}
            />
          ) : <Empty text="No scans yet." />}
        </Panel>

        <Panel icon={<FiTrendingUp className="text-secondary" />} title="Scans Over Time" className="lg:col-span-2" delay={0.2}>
          {dash.scansPerDay.length ? (
            <Line
              data={{ labels: dash.scansPerDay.map((d) => d.date), datasets: [{ label: 'Scans', data: dash.scansPerDay.map((d) => d.count), borderColor: '#a78bfa', backgroundColor: '#a78bfa', tension: 0.3 }] }}
              options={{ plugins: { legend }, scales: { x: axis, y: { ...axis, beginAtZero: true, ticks: { ...axis.ticks, precision: 0 } } } }}
            />
          ) : <Empty text="No scans yet." />}
        </Panel>

        <Panel icon={<FiList className="text-warning" />} title="Top Triggered Checks" className="lg:col-span-2" delay={0.3}>
          {dash.topChecks.length ? (
            <Bar
              data={{ labels: dash.topChecks.map((c) => c.name), datasets: [{ label: 'Scans', data: dash.topChecks.map((c) => c.count), backgroundColor: '#fbbf24' }] }}
              options={{ indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { ...axis, beginAtZero: true, ticks: { ...axis.ticks, precision: 0 } }, y: axis } }}
            />
          ) : <Empty text="No checks triggered yet." />}
        </Panel>

        <Panel icon={<FiCpu className="text-primary" />} title="Model Metrics (test set)" delay={0.4}>
          {metrics ? (
            <div className="space-y-3 text-sm">
              {[['Accuracy', metrics.accuracy], ['Precision', metrics.precision], ['Recall', metrics.recall], ['F1-score', metrics.f1], ['ROC-AUC', metrics.roc_auc]].map(([k, v]) => (
                <div key={k} className="flex justify-between bg-white/5 px-4 py-2 rounded-xl border border-white/5">
                  <span className="text-gray-400">{k}</span><span className="text-white font-semibold">{k === 'ROC-AUC' ? v : pct(v)}</span>
                </div>
              ))}
              {cm && (
                <div className="text-xs text-gray-400 pt-2">
                  Confusion matrix (rows = actual legit / phishing): [{cm[0].join(', ')}] / [{cm[1].join(', ')}]
                </div>
              )}
              <div className="text-xs text-gray-500">
                Train {metrics.train_size} / test {metrics.test_size} emails · {metrics.dataset}
              </div>
            </div>
          ) : <Empty text={metrics === false ? 'Not available (model not trained).' : 'Loading...'} />}
        </Panel>

        <Panel icon={<FiDatabase className="text-secondary" />} title="Indicators of Compromise" className="lg:col-span-3" delay={0.5}>
          <p className="text-gray-500 text-xs -mt-3 mb-4">
            Every domain, URL, IP and attachment hash seen in scanned emails. The verdict is that of the worst email it appeared in, not a verdict on the indicator itself.
          </p>
          {iocs.length ? (
            <div className="overflow-x-auto max-h-[480px] overflow-y-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-gray-400 border-b border-white/10 sticky top-0 bg-background">
                  <tr>
                    <th className="px-4 py-3 font-medium">Value</th>
                    <th className="px-4 py-3 font-medium">Type</th>
                    <th className="px-4 py-3 font-medium text-right">Hits</th>
                    <th className="px-4 py-3 font-medium text-right">Seen in (worst email verdict)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {iocs.map((i) => (
                    <tr key={`${i.type}:${i.value}`} className="hover:bg-white/5">
                      <td className="px-4 py-3 text-gray-300 truncate max-w-md">{i.value}</td>
                      <td className="px-4 py-3 text-gray-400">{i.type}</td>
                      <td className="px-4 py-3 text-right text-gray-300">{i.hits}</td>
                      <td className="px-4 py-3 text-right font-semibold" style={{ color: COLORS[i.verdict] }}>{i.verdict}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <Empty text="No indicators recorded yet." />}
        </Panel>
      </div>
    </div>
  );
};

export default AnalyticsPage;
