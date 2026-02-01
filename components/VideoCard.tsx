import React from 'react';
import { Download, Play, Clock, AlertTriangle, ShieldCheck } from 'lucide-react';
import { VideoData } from '../types';
import { getDownloadLink } from '../services/api';

interface VideoCardProps {
  data: VideoData;
}

const VideoCard: React.FC<VideoCardProps> = ({ data }) => {
  const downloadLink = getDownloadLink(data);

  // Helper to format duration seconds into MM:SS
  const formatDuration = (seconds: number | null) => {
    if (!seconds) return 'N/A';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  return (
    <div className="w-full max-w-3xl mt-16 perspective-1000 z-10">
      {data.isMock && (
        <div className="mb-6 p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl flex items-center gap-4 text-amber-200 text-sm backdrop-blur-md animate-bounce-short">
          <div className="p-2 bg-amber-500/20 rounded-full">
            <AlertTriangle size={20} className="text-amber-500 shrink-0" />
          </div>
          <div>
            <span className="font-bold text-base block mb-1">Backend Disconnected</span>
            <span className="opacity-80">You are viewing demo data. Local Python server is offline.</span>
          </div>
        </div>
      )}

      {/* 3D Card Container */}
      <div className="group relative transition-all duration-500 hover:rotate-y-2 hover:scale-[1.02]">
        {/* Glow Effect */}
        <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-500 via-purple-500 to-pink-500 rounded-3xl blur opacity-30 group-hover:opacity-75 transition duration-500"></div>
        
        <div className="relative bg-black/80 backdrop-blur-xl border border-white/10 rounded-[22px] overflow-hidden shadow-2xl">
          <div className="flex flex-col md:flex-row">
            
            {/* Thumbnail Section */}
            <div className="md:w-5/12 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent z-10"></div>
              <img 
                src={data.thumbnail} 
                alt={data.title} 
                className="w-full h-full object-cover min-h-[240px] group-hover:scale-110 transition-transform duration-700 ease-out"
              />
              
              <div className="absolute inset-0 z-20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300 backdrop-blur-[2px]">
                <div className="w-16 h-16 bg-white/20 backdrop-blur-md rounded-full flex items-center justify-center border border-white/30 shadow-[0_0_30px_rgba(255,255,255,0.2)]">
                  <Play className="text-white fill-white ml-1" size={32} />
                </div>
              </div>

              <div className="absolute bottom-3 right-3 z-20 bg-black/60 backdrop-blur-md border border-white/10 text-white text-xs font-bold px-3 py-1.5 rounded-lg flex items-center gap-1.5">
                <Clock size={14} className="text-cyan-400" />
                {formatDuration(data.duration)}
              </div>
            </div>

            {/* Content Section */}
            <div className="md:w-7/12 p-8 flex flex-col justify-between relative overflow-hidden">
              {/* Decorative background element */}
              <div className="absolute top-0 right-0 w-64 h-64 bg-fuchsia-600/10 rounded-full blur-3xl -mr-32 -mt-32 pointer-events-none"></div>

              <div>
                <div className="flex items-center gap-3 mb-4">
                  <span className={`px-3 py-1 rounded-lg text-[11px] font-extrabold uppercase tracking-widest border shadow-lg ${
                    data.isMock 
                      ? 'bg-amber-500/20 text-amber-300 border-amber-500/50 shadow-amber-900/20' 
                      : 'bg-cyan-500/20 text-cyan-300 border-cyan-500/50 shadow-cyan-900/20'
                  }`}>
                    {data.platform || 'Video'}
                  </span>
                  <span className="px-3 py-1 rounded-lg text-[11px] font-extrabold uppercase tracking-widest bg-pink-500/20 text-pink-300 border border-pink-500/50 shadow-lg shadow-pink-900/20">
                    {data.ext.toUpperCase()}
                  </span>
                </div>
                
                <h3 className="text-2xl font-black text-white leading-snug line-clamp-2 mb-3 drop-shadow-lg" title={data.title}>
                  {data.title}
                </h3>
              </div>

              <div className="mt-8 space-y-4">
                <a 
                  href={downloadLink}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="relative overflow-hidden w-full flex items-center justify-center gap-3 bg-white text-black font-black py-4 px-6 rounded-xl transition-all hover:scale-[1.02] active:scale-[0.98] group/btn"
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-cyan-400 via-fuchsia-400 to-cyan-400 opacity-0 group-hover/btn:opacity-100 transition-opacity duration-300 bg-[length:200%_auto] animate-gradient-xy"></div>
                  <div className="absolute inset-[2px] bg-white rounded-[10px] group-hover/btn:bg-opacity-95 transition-colors"></div>
                  <span className="relative z-10 flex items-center gap-2">
                    <Download size={22} className="group-hover/btn:animate-bounce" />
                    DOWNLOAD NOW
                  </span>
                </a>
                
                <div className="flex items-center justify-center gap-2 text-xs text-slate-400 font-medium">
                  <ShieldCheck size={14} className="text-emerald-400" />
                  <span>Secure • No Watermark • Ultra HD</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VideoCard;