import React, { useState, useEffect } from 'react';
import UploadZone from '../components/scanner/UploadZone';
import ScanResults from '../components/scanner/ScanResults';
import ScanningProgress from '../components/scanner/ScanningProgress';
import api, { errorMessage } from '../utils/api';
import { FiSearch, FiRefreshCw } from 'react-icons/fi';

const EmailScannerPage = () => {
  const [file, setFile] = useState(null);
  
  // Real-time task state
  const [scanId, setScanId] = useState(null);
  const [statusObj, setStatusObj] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);

  // Polling effect
  useEffect(() => {
    let intervalId;
    
    if (scanId && isScanning) {
      intervalId = setInterval(async () => {
        try {
          const res = await api.get(`/scanner/status/${scanId}`);
          setStatusObj(res.data);
          
          if (res.data.status === 'completed') {
            setIsScanning(false);
            setResults(res.data.result);
            clearInterval(intervalId);
          } else if (res.data.status === 'failed') {
            setIsScanning(false);
            setError("Scan pipeline failed.");
            clearInterval(intervalId);
          }
        } catch (err) {
          setIsScanning(false);
          setError(errorMessage(err, 'Could not fetch scan status.'));
          clearInterval(intervalId);
        }
      }, 1000); // Poll every 1 second
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [scanId, isScanning]);

  const reset = () => {
    setFile(null);
    setScanId(null);
    setStatusObj(null);
    setResults(null);
    setError(null);
  };

  const handleScan = async () => {
    if (!file) return;
    
    setIsScanning(true);
    setError(null);
    setResults(null);
    setStatusObj({ status: 'processing', current_step: 'init', logs: ['[System] Uploading file to the analysis API...'] });
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await api.post('/scanner/upload-email', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setScanId(response.data.scan_id);
    } catch (err) {
      console.error(err);
      setError(errorMessage(err, 'An error occurred during scanning.'));
      setIsScanning(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-20 pt-8">
      <div className="mb-10 text-center">
        <h1 className="text-4xl font-bold mb-3 text-white">Deep Threat Analysis</h1>
        <p className="text-gray-300 max-w-2xl mx-auto">Upload raw .eml data to initialize AI threat detection protocols and uncover hidden malicious intent.</p>
      </div>
      
      <div className="grid grid-cols-1 gap-8">
        {!isScanning && !results && (
          <UploadZone onFileSelected={(f) => setFile(f)} />
        )}
        
        {file && !isScanning && !results && (
          <div className="flex justify-center mt-6">
            <button 
              onClick={handleScan}
              className="glass-button-primary px-10 py-4 text-lg flex items-center gap-3"
            >
              <FiSearch className="text-xl" />
              Analyze Payload
            </button>
          </div>
        )}

        {statusObj && (
          <ScanningProgress 
            status={statusObj.status} 
            currentStep={statusObj.current_step} 
            logs={statusObj.logs || []} 
          />
        )}

        {error && (
          <div className="glass-panel-danger p-6 text-center">
            <p className="text-danger font-medium">{error}</p>
          </div>
        )}

        {results && !isScanning && (
          <ScanResults results={results} />
        )}

        {(results || error) && !isScanning && (
          <div className="flex justify-center">
            <button onClick={reset} className="glass-button-primary px-10 py-4 text-lg flex items-center gap-3">
              <FiRefreshCw className="text-xl" />
              Scan another email
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default EmailScannerPage;
