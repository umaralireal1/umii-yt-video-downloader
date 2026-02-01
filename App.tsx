import React, { useState } from 'react';
import SearchBar from './components/SearchBar';
import VideoCard from './components/VideoCard';
import Loader from './components/Loader';
import Footer from './components/Footer';
import { fetchVideoInfo } from './services/api';
import { VideoData } from './types';
import { Zap, ShieldCheck, Layers, Star } from 'lucide-react';

function App() {
  const [videoData, setVideoData] = useState<VideoData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (url: string) => {
    setIsLoading(true);
    setError(null);
    setVideoData(null);

    try {
      const data = await fetchVideoInfo(url);
      setVideoData(data);
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden bg-black text-slate-200 font-sans selection:bg-fuchsia-500/30 selection:text-fuchsia-200">
      
      {/* Background Ambience - 3D Aurora Effect */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-purple-900/20 blur-[120px] animate-float" style={{ animationDuration: '10s' }}></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-cyan-900/20 blur-[120px] animate-float" style={{ animationDuration: '15s', animationDelay: '-5s' }}></div>
        <div className="absolute top-[40%] left-[50%] transform -translate-x-1/2 w-[60%] h-[60%] rounded-full bg-fuchsia-900/10 blur-[100px] animate-pulse" style={{ animationDuration: '8s' }}></div>
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 brightness-100 contrast-150 mix-blend-overlay"></div>
      </div>

      <main className="flex-1 flex flex-col items-center px-4 pt-24 pb-12 w-full max-w-6xl mx-auto relative z-10">
        
        {/* Header Section */}
        <div className="text-center mb-16 space-y-6 animate-float perspective-1000">
          
          <div className="inline-flex items-center justify-center gap-2 px-4 py-1.5 bg-white/5 backdrop-blur-md rounded-full border border-white/10 mb-6 hover:scale-105 transition-transform cursor-default shadow-[0_0_15px_rgba(255,255,255,0.05)]">
            <Star size={12} className="text-yellow-400 fill-yellow-400" />
            <span className="text-slate-300 text-xs font-bold tracking-widest uppercase">
              Official Release v2.0
            </span>
          </div>

          <h1 className="text-6xl md:text-8xl font-black tracking-tight text-white mb-2 drop-shadow-2xl">
            Umii <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-fuchsia-400 to-purple-500 animate-gradient-xy">Downloader</span>
          </h1>
          
          <p className="text-xl text-slate-400 max-w-2xl mx-auto font-light leading-relaxed">
            The ultimate tool to extract <span className="text-white font-semibold">4K video & audio</span> from TikTok, YouTube, and Instagram. 
            <br className="hidden md:block"/>
            <span className="text-cyan-400">No Watermarks.</span> <span className="text-fuchsia-400">Unlimited Speeds.</span>
          </p>
        </div>

        {/* Input Section */}
        <SearchBar onSearch={handleSearch} isLoading={isLoading} />

        {/* Dynamic Content Area */}
        <div className="w-full flex flex-col items-center min-h-[400px] mt-12">
          {isLoading && <Loader />}
          
          {error && (
            <div className="w-full max-w-2xl mt-8 p-6 bg-red-500/10 backdrop-blur-md border border-red-500/20 rounded-2xl text-red-200 text-center animate-bounce-short shadow-[0_0_30px_rgba(239,68,68,0.1)]">
              <p className="font-bold text-lg mb-1">Oops! Something went wrong.</p>
              <p className="text-sm opacity-80">{error}</p>
            </div>
          )}

          {videoData && !isLoading && <VideoCard data={videoData} />}

          {!videoData && !isLoading && !error && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-20 w-full text-slate-400">
              <Feature 
                icon={<Zap className="text-yellow-400" />} 
                title="Supercharged Speed" 
                desc="Powered by elite cloud servers for instant processing." 
                delay="0ms"
              />
              <Feature 
                icon={<ShieldCheck className="text-emerald-400" />} 
                title="Privacy First" 
                desc="End-to-end encryption. No logs. Completely anonymous." 
                delay="100ms"
              />
              <Feature 
                icon={<Layers className="text-blue-400" />} 
                title="Universal Support" 
                desc="Works perfectly with TikTok, IG Reels, Shorts & more." 
                delay="200ms"
              />
            </div>
          )}
        </div>
      </main>
      
      <Footer />
    </div>
  );
}

const Feature: React.FC<{icon: React.ReactNode, title: string, desc: string, delay: string}> = ({ icon, title, desc, delay }) => (
  <div 
    className="bg-white/5 backdrop-blur-sm p-8 rounded-3xl border border-white/5 hover:bg-white/10 hover:border-white/20 transition-all duration-500 group hover:-translate-y-2"
    style={{ animationDelay: delay }}
  >
    <div className="mb-6 bg-gradient-to-br from-slate-800 to-black w-14 h-14 rounded-2xl flex items-center justify-center border border-white/10 shadow-lg group-hover:scale-110 transition-transform duration-500 group-hover:shadow-[0_0_20px_rgba(255,255,255,0.1)]">
      {icon}
    </div>
    <h3 className="text-white text-lg font-bold mb-3 group-hover:text-cyan-300 transition-colors">{title}</h3>
    <p className="text-sm leading-relaxed opacity-80 group-hover:opacity-100 transition-opacity">{desc}</p>
  </div>
);

export default App;