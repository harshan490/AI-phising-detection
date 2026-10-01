import React, { useState } from 'react';
import { FiUploadCloud, FiFileText } from 'react-icons/fi';
import { motion } from 'framer-motion';

const UploadZone = ({ onFileSelected }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true);
    } else if (e.type === 'dragleave') {
      setIsDragging(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      handleFile(file);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file) => {
    if (!file.name.endsWith('.eml')) {
      alert('Invalid file type. Only .eml files are permitted.');
      return;
    }
    setSelectedFile(file);
    onFileSelected(file);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`glass-panel relative flex flex-col items-center justify-center transition-all duration-300 border-2 border-dashed ${
        isDragging ? 'bg-white/10 border-primary/50 scale-[1.02]' : 'border-white/20 hover:border-white/40'
      }`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      style={{ minHeight: '300px' }}
    >
      <input
        type="file"
        id="file-upload"
        className="hidden"
        accept=".eml"
        onChange={handleChange}
      />
      
      {!selectedFile ? (
        <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center text-center w-full h-full justify-center p-8 z-10">
          <div className="w-20 h-20 rounded-full bg-white/5 border border-white/10 shadow-inner flex items-center justify-center text-primary mb-6 transition-transform group-hover:scale-110 duration-300">
            <FiUploadCloud className="text-4xl" />
          </div>
          <h3 className="text-2xl font-semibold mb-2 text-white">Upload Email File</h3>
          <p className="text-gray-400 text-sm mb-8 max-w-sm">Drag and drop your raw .eml file here or click to browse your computer.</p>
          <div className="glass-button px-8 py-2 text-sm rounded-full">
            Browse Files
          </div>
        </label>
      ) : (
        <div className="flex flex-col items-center text-center w-full p-8 z-10">
          <div className="w-20 h-20 rounded-full bg-white/10 border border-white/20 flex items-center justify-center text-primary mb-6 shadow-[0_0_20px_rgba(255,255,255,0.1)]">
            <FiFileText className="text-4xl text-primary" />
          </div>
          <h3 className="text-xl font-semibold text-white truncate max-w-sm">{selectedFile.name}</h3>
          <p className="text-sm text-gray-400 mt-2">File size: {(selectedFile.size / 1024).toFixed(1)} KB</p>
          
          <button 
            onClick={() => { setSelectedFile(null); onFileSelected(null); }}
            className="mt-8 text-sm text-danger hover:text-white border border-danger/30 hover:border-danger hover:bg-danger/80 px-6 py-2 rounded-full transition-colors"
          >
            Remove File
          </button>
        </div>
      )}
    </motion.div>
  );
};

export default UploadZone;
