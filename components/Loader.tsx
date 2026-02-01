import React from 'react';

const Loader: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center space-y-4 py-12">
      <div className="relative">
        <div className="h-16 w-16 rounded-full border-4 border-slate-700 border-t-cyan-500 animate-spin"></div>
        <div className="absolute top-0 left-0 h-16 w-16 rounded-full border-4 border-transparent border-b-fuchsia-500 animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}></div>
      </div>
      <p className="text-slate-400 text-sm animate-pulse">Analyzing URL & Extracting Metadata...</p>
    </div>
  );
};

export default Loader;