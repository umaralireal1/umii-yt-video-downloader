import React, { useState } from 'react';
import { Search, Link as LinkIcon, X, Sparkles } from 'lucide-react';

interface SearchBarProps {
  onSearch: (url: string) => void;
  isLoading: boolean;
}

const SearchBar: React.FC<SearchBarProps> = ({ onSearch, isLoading }) => {
  const [url, setUrl] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) {
      onSearch(url.trim());
    }
  };

  const clearInput = () => setUrl('');

  return (
    <div className="w-full max-w-2xl perspective-1000 z-20 px-2 sm:px-0">
      <form 
        onSubmit={handleSubmit} 
        className={`
          relative group transition-all duration-500 transform
          ${isFocused ? 'scale-105 sm:rotate-x-2' : 'hover:scale-[1.01]'}
        `}
      >
        {/* Animated Glow Background */}
        <div className="absolute -inset-1 bg-gradient-to-r from-pink-600 via-purple-600 to-cyan-600 rounded-2xl blur opacity-30 group-hover:opacity-100 animate-gradient-xy transition duration-1000"></div>
        
        {/* Glass Container */}
        <div className="relative flex items-center bg-black/60 backdrop-blur-xl border border-white/10 rounded-2xl p-1.5 sm:p-2 shadow-2xl overflow-hidden">
          
          <div className="pl-3 pr-2 text-fuchsia-400 hidden xs:block">
            <LinkIcon size={20} />
          </div>
          
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder="Paste link here..."
            className="flex-1 min-w-0 bg-transparent text-white placeholder-slate-500 outline-none h-12 sm:h-14 px-2 font-medium text-base sm:text-lg"
            disabled={isLoading}
          />

          {url && (
            <button
              type="button"
              onClick={clearInput}
              className="p-2 text-slate-400 hover:text-white transition-colors shrink-0"
            >
              <X size={18} />
            </button>
          )}

          <button
            type="submit"
            disabled={isLoading || !url}
            className={`
              ml-1 sm:ml-2 px-4 sm:px-8 h-10 sm:h-12 rounded-xl font-bold flex items-center gap-2 transition-all duration-300 transform shrink-0
              ${isLoading || !url 
                ? 'bg-slate-800/50 text-slate-500 cursor-not-allowed' 
                : 'bg-gradient-to-r from-fuchsia-600 to-purple-600 hover:from-fuchsia-500 hover:to-purple-500 text-white shadow-[0_0_15px_rgba(192,38,211,0.3)] hover:shadow-[0_0_25px_rgba(192,38,211,0.6)] active:scale-95'
              }
            `}
          >
            {isLoading ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            ) : (
              <>
                <Sparkles size={16} className={url ? "animate-pulse" : ""} />
                <span className="text-sm sm:text-base">Fetch</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default SearchBar;