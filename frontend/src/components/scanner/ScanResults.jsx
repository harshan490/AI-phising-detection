import React from 'react';
import { motion } from 'framer-motion';
import { FiShield, FiAlertOctagon, FiAlertTriangle, FiFileText, FiLink, FiCpu, FiList, FiBarChart2, FiPaperclip } from 'react-icons/fi';

const VERDICT_STYLE = {
  Phishing: { title: 'Phishing Detected', color: 'text-danger', bar: 'bg-danger', panel: 'glass-panel-danger', icon: <FiAlertOctagon className="animate-pulse" /> },
  Suspicious: { title: 'Suspicious Email', color: 'text-warning', bar: 'bg-warning', panel: 'glass-panel', icon: <FiAlertTriangle /> },
  Safe: { title: 'No Threat Indicators', color: 'text-primary', bar: 'bg-primary', panel: 'glass-panel', icon: <FiShield /> },
};

const COMPONENT_LABELS = {
  text: 'AI text model',
  url: 'URL checks',
  auth: 'SPF / DKIM / DMARC',
  attachment: 'Attachments',
  sender: 'Sender checks',
};

const authColor = (v) => (v === 'pass' ? 'text-primary' : v === 'none' ? 'text-warning' : 'text-danger');

const ScanResults = ({ results }) => {
  if (!results) return null;

  const style = VERDICT_STYLE[results.verdict] || VERDICT_STYLE.Safe;
  const components = results.components || {};
  const weights = results.weights || {};
  const triggered = results.triggered_checks || [];
  const terms = results.top_terms || results.xai_reasons || [];
  const ti = results.threat_intel || {};
  const urlIntel = ti.url_results || [];

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6 font-sans">
      {/* Top Banner */}
      <div className={`${style.panel} p-8 flex flex-col md:flex-row items-center justify-between gap-6 relative overflow-hidden`}>
        <div className={`absolute top-0 right-0 w-64 h-64 rounded-full blur-[100px] opacity-20 -z-10 ${style.bar}`}></div>
        <div className="flex items-center gap-6 z-10">
          <div className={`w-20 h-20 rounded-full flex items-center justify-center text-4xl bg-white/5 border border-white/10 shadow-lg ${style.color}`}>
            {style.icon}
          </div>
          <div>
            <h2 className={`text-2xl font-bold ${style.color}`}>{style.title}</h2>
            <p className="text-gray-400 mt-1 font-medium">Verdict: {results.verdict}</p>
            <p className="text-gray-500 mt-1 text-xs">
              AI text model phishing probability: {((results.text_probability ?? 0) * 100).toFixed(1)}%
            </p>
          </div>
        </div>
        <div className="flex flex-col items-end z-10">
          <span className="text-gray-400 text-sm mb-1 font-medium">Risk Score</span>
          <div className={`text-5xl font-bold ${style.color} drop-shadow-md`}>
            {results.risk_score?.toFixed(1)}<span className="text-2xl text-gray-400">/100</span>
          </div>
          <span className="text-gray-500 text-xs mt-1">Safe &lt; 40 ≤ Suspicious &lt; 70 ≤ Phishing</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk components */}
        <div className="glass-panel p-8">
          <h3 className="text-lg font-semibold mb-6 flex items-center gap-2 text-white border-b border-white/10 pb-4">
            <FiBarChart2 className="text-secondary" /> Risk Components
          </h3>
          <div className="space-y-5">
            {Object.keys(COMPONENT_LABELS).map((key) => {
              const v = components[key] ?? 0;
              return (
                <div key={key} className="flex flex-col gap-2">
                  <div className="flex justify-between text-sm font-medium">
                    <span className="text-gray-300">{COMPONENT_LABELS[key]} <span className="text-gray-500 text-xs">× {weights[key]}</span></span>
                    <span className={v >= 0.7 ? 'text-danger' : v >= 0.4 ? 'text-warning' : 'text-primary'}>{(v * 100).toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-white/5 rounded-full h-2 overflow-hidden border border-white/5">
                    <div className={`h-full rounded-full ${v >= 0.7 ? 'bg-danger' : v >= 0.4 ? 'bg-warning' : 'bg-primary'}`} style={{ width: `${Math.max(v * 100, 1)}%` }} />
                  </div>
                </div>
              );
            })}
            {(results.overrides || []).map((o) => (
              <p key={o} className="text-danger text-xs font-medium">{o}</p>
            ))}
          </div>
        </div>

        {/* Top terms */}
        <div className="glass-panel p-8">
          <h3 className="text-lg font-semibold mb-6 flex items-center gap-2 text-white border-b border-white/10 pb-4">
            <FiCpu className="text-secondary" /> Model Explanation (top terms)
          </h3>
          <div className="space-y-5">
            {terms.length > 0 ? (
              terms.map((reason, idx) => (
                <div key={idx} className="flex flex-col gap-2">
                  <div className="flex justify-between text-sm font-medium">
                    <span className="text-gray-300">"{reason.feature}"</span>
                    <span className={reason.weight > 0 ? 'text-danger' : 'text-primary'}>
                      {reason.weight > 0 ? '+' : ''}{reason.weight.toFixed(3)}
                    </span>
                  </div>
                  <div className="w-full bg-white/5 rounded-full h-2 overflow-hidden border border-white/5">
                    <div className={`h-full rounded-full ${reason.weight > 0 ? 'bg-danger' : 'bg-primary'}`}
                      style={{ width: `${Math.min(Math.abs(reason.weight) * 100, 100)}%` }} />
                  </div>
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-sm">Not available.</p>
            )}
            <p className="text-gray-500 text-xs">Positive = pushes towards phishing. TF-IDF weight × logistic-regression coefficient.</p>
          </div>
        </div>

        {/* Triggered checks */}
        <div className="glass-panel p-8 lg:col-span-2">
          <h3 className="text-lg font-semibold mb-6 flex items-center gap-2 text-white border-b border-white/10 pb-4">
            <FiList className="text-secondary" /> Triggered Checks <span className="text-gray-500 text-xs font-normal">(local heuristics)</span>
          </h3>
          {triggered.length > 0 ? (
            <div className="space-y-3">
              {triggered.map((c) => (
                <div key={c.id} className="flex items-start justify-between gap-4 bg-white/5 p-4 rounded-xl border border-white/5 text-sm">
                  <div className="min-w-0">
                    <div className="text-gray-100 font-medium">{c.name} <span className="text-gray-500 text-xs">[{c.category}]</span></div>
                    <div className="text-gray-400 text-xs mt-1 break-words">{c.evidence}</div>
                  </div>
                  <span className={`shrink-0 font-semibold ${c.severity >= 0.7 ? 'text-danger' : c.severity >= 0.4 ? 'text-warning' : 'text-gray-300'}`}>
                    {(c.severity * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No heuristic checks triggered.</p>
          )}
        </div>

        {/* Email Headers Info */}
        <div className="glass-panel p-8">
          <h3 className="text-lg font-semibold mb-6 flex items-center gap-2 text-white border-b border-white/10 pb-4">
            <FiFileText className="text-secondary" /> Email Metadata
          </h3>
          <div className="space-y-5 text-sm">
            <div className="flex flex-col bg-white/5 p-4 rounded-xl border border-white/5">
              <span className="text-gray-400 mb-1">Sender</span>
              <span className="text-gray-100 font-medium truncate">{results.headers?.sender || 'Unknown'}</span>
            </div>
            <div className="flex flex-col bg-white/5 p-4 rounded-xl border border-white/5">
              <span className="text-gray-400 mb-1">Subject</span>
              <span className="text-gray-100 font-medium truncate">{results.headers?.subject || 'No Subject'}</span>
            </div>
            <div className="pt-2">
              <span className="text-gray-400 mb-3 block font-medium">Authentication-Results header</span>
              <div className="flex justify-between items-center bg-white/5 border border-white/10 p-4 rounded-xl">
                {['spf', 'dkim', 'dmarc'].map((m, i) => (
                  <div key={m} className={`flex flex-col items-center ${i === 1 ? 'border-l border-r border-white/10 px-8' : ''}`}>
                    <span className="text-gray-500 text-xs mb-1">{m.toUpperCase()}</span>
                    <span className={`font-semibold ${authColor(results.headers?.[m])}`}>{results.headers?.[m]?.toUpperCase() || 'N/A'}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Attachments */}
        <div className="glass-panel p-8">
          <h3 className="text-lg font-semibold mb-6 flex items-center gap-2 text-white border-b border-white/10 pb-4">
            <FiPaperclip className="text-secondary" /> Attachments
          </h3>
          {(results.attachments || []).length > 0 ? (
            <div className="space-y-3 text-sm">
              {results.attachments.map((a, i) => (
                <div key={i} className="bg-white/5 p-4 rounded-xl border border-white/5">
                  <div className="text-gray-100 font-medium">{a.filename} <span className="text-gray-500 text-xs">({a.content_type}, {a.size} bytes)</span></div>
                  <div className="text-gray-500 text-xs mt-1 break-all">SHA-256 {a.sha256}</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No attachments.</p>
          )}
        </div>

        {/* Threat Intel URLs */}
        <div className="glass-panel p-8 lg:col-span-2">
          <h3 className="text-lg font-semibold mb-2 flex items-center gap-2 text-white">
            <FiLink className="text-secondary" /> Extracted URLs & Threat Intel
          </h3>
          <p className="text-gray-500 text-xs mb-6 border-b border-white/10 pb-4">
            {ti.source || 'Local threat intel (offline)'} · External: {ti.external?.status || 'Not available'}
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-gray-400 font-medium border-b border-white/10">
                <tr>
                  <th className="px-4 py-3 font-medium">URL Target</th>
                  <th className="px-4 py-3 font-medium">Domain</th>
                  <th className="px-4 py-3 text-right font-medium">Local blocklist</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {urlIntel.length > 0 ? (
                  urlIntel.map((t, idx) => (
                    <tr key={idx} className="hover:bg-white/5 transition-colors">
                      <td className="px-4 py-4 text-gray-300 truncate max-w-xs">{t.url}</td>
                      <td className="px-4 py-4 text-gray-400">{t.domain}</td>
                      <td className="px-4 py-4 text-right">
                        <span className={`px-3 py-1 text-xs font-semibold rounded-full border ${t.malicious ? 'bg-danger/10 text-danger border-danger/20' : 'bg-white/5 text-gray-300 border-white/10'}`}>
                          {t.malicious ? 'Listed' : 'Not listed'}
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="3" className="px-4 py-8 text-center text-gray-500">No external links found in payload.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default ScanResults;
