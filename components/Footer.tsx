import React from 'react';
import { Facebook, Phone, Heart } from 'lucide-react';

const Footer: React.FC = () => {
  return (
    <footer className="w-full relative mt-auto border-t border-white/5 bg-black/80 backdrop-blur-xl z-30">
      {/* Decorative Top Border */}
      <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-fuchsia-500 to-transparent opacity-50"></div>
      
      <div className="container mx-auto px-6 py-10">
        <div className="flex flex-col md:flex-row items-center justify-between gap-8">
          
          {/* Brand Info */}
          <div className="text-center md:text-left">
            <h2 className="text-2xl font-black text-white tracking-tight mb-2">
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-fuchsia-500">Umii</span> Video Downloader
            </h2>
            <p className="text-slate-400 text-sm max-w-xs leading-relaxed">
              Premium 3D Video Extraction Tool. 
              <br />Fast, Secure, and Always Free.
            </p>
          </div>

          {/* Contact & Socials */}
          <div className="flex flex-col items-center md:items-end gap-4">
            <div className="flex items-center gap-4">
              <a 
                href="https://wa.me/923168432329" 
                target="_blank" 
                rel="noreferrer"
                className="group flex items-center gap-3 px-5 py-2.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 hover:bg-emerald-500/20 hover:border-emerald-500/50 transition-all hover:scale-105"
              >
                <Phone size={18} className="text-emerald-400 group-hover:rotate-12 transition-transform" />
                <span className="text-emerald-300 font-bold text-sm">+92 316 8432329</span>
              </a>

              <a 
                href="https://www.facebook.com/share/1A4o8XNGpu/" 
                target="_blank" 
                rel="noreferrer"
                className="group flex items-center justify-center w-10 h-10 rounded-full bg-blue-600/10 border border-blue-600/20 hover:bg-blue-600/20 hover:border-blue-600/50 hover:scale-110 transition-all"
              >
                <Facebook size={20} className="text-blue-400" />
              </a>

              <a 
                href="https://www.tiktok.com/@umarali_real" 
                target="_blank" 
                rel="noreferrer"
                className="group flex items-center justify-center w-10 h-10 rounded-full bg-black border border-slate-700 hover:border-fuchsia-500 hover:scale-110 transition-all overflow-hidden relative"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-cyan-500 to-fuchsia-600 opacity-20 group-hover:opacity-40 transition-opacity"></div>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5 text-white z-10">
                  <path d="M9 12a4 4 0 1 0 4 4V4a5 5 0 0 0 5 5" />
                </svg>
              </a>
            </div>
            
            <div className="text-xs font-medium text-slate-500 flex items-center gap-1.5">
               Powered By <span className="text-fuchsia-400 font-bold">Umar Ali</span>
               <Heart size={10} className="text-red-500 fill-red-500 animate-pulse" />
            </div>
          </div>

        </div>
        
        <div className="mt-8 pt-6 border-t border-white/5 text-center text-slate-600 text-[10px] uppercase tracking-wider">
          &copy; {new Date().getFullYear()} Umii Services. All rights reserved.
        </div>
      </div>
    </footer>
  );
};

export default Footer;