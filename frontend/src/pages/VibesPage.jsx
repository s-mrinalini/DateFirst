import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { Heart, MapPin, X, Check, Sparkles } from 'lucide-react';
import { Button } from '../components/ui/button';
import { formatName } from '../lib/displayName';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function VibesPage() {
  const [vibes, setVibes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchVibes();
  }, []);

  const fetchVibes = async () => {
    try {
      const response = await axios.get(`${API}/vibes`);
      setVibes(response.data.vibes);
    } catch (error) {
      toast.error('Failed to load vibes');
    } finally {
      setLoading(false);
    }
  };

  const handleLikeBack = async (userId) => {
    try {
      const response = await axios.post(`${API}/like/${userId}`);
      
      if (response.data.is_match) {
        toast.success("🎉 It's a match!", {
          description: 'Go to Plans to start chatting!'
        });
      }
      
      setVibes(prev => prev.filter(v => v.user_id !== userId));
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed');
    }
  };

  const handlePass = (userId) => {
    setVibes(prev => prev.filter(v => v.user_id !== userId));
  };

  if (loading) {
    return (
      <div className="p-4">
        <div className="h-8 bg-stone-200 rounded w-1/3 mb-6 animate-pulse" />
        <div className="grid grid-cols-2 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white rounded-2xl overflow-hidden shadow animate-pulse">
              <div className="aspect-square bg-stone-200" />
              <div className="p-3 space-y-2">
                <div className="h-4 bg-stone-200 rounded w-1/2" />
                <div className="h-3 bg-stone-200 rounded w-2/3" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FDFCF8] p-4">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
          Vibes
        </h1>
        <p className="text-[#57534E] text-sm mt-1">
          People who liked your invite
        </p>
      </div>

      {vibes.length > 0 ? (
        <div className="grid grid-cols-2 gap-4">
          {vibes.map((vibe, idx) => (
            <div 
              key={vibe.user_id}
              className="bg-white rounded-2xl overflow-hidden shadow-md animate-slideUp"
              style={{ animationDelay: `${idx * 0.05}s` }}
              data-testid={`vibe-${vibe.user_id}`}
            >
              <div className="relative aspect-square bg-stone-100">
                {vibe.main_photo ? (
                  <img
                    src={vibe.main_photo}
                    alt={vibe.first_name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-[#E76F51] to-[#E9C46A]">
                    <span className="text-white text-5xl font-bold">
                      {vibe.first_name?.charAt(0).toUpperCase() || '?'}
                    </span>
                  </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
                <div className="absolute bottom-2 left-2 text-white">
                  <p className="font-bold">{formatName(vibe)}</p>
                  <div className="flex items-center gap-1 text-xs text-white/80">
                    <MapPin className="w-3 h-3" />
                    <span>{vibe.city}</span>
                  </div>
                </div>
              </div>

              <div className="p-3">
                <p className="text-xs text-[#E76F51] font-medium mb-1">
                  {vibe.first_date_idea?.title}
                </p>
                <p className="text-xs text-[#57534E] line-clamp-2">
                  {vibe.first_date_idea?.description}
                </p>

                <div className="flex gap-2 mt-3">
                  <button
                    onClick={() => handlePass(vibe.user_id)}
                    className="flex-1 py-2 rounded-full border border-stone-200 text-[#A8A29E] hover:border-red-300 hover:text-red-500 transition-all"
                    data-testid={`vibe-pass-${vibe.user_id}`}
                  >
                    <X className="w-4 h-4 mx-auto" />
                  </button>
                  <button
                    onClick={() => handleLikeBack(vibe.user_id)}
                    className="flex-1 py-2 rounded-full bg-[#E76F51] text-white hover:bg-[#D65D40] transition-all"
                    data-testid={`vibe-like-${vibe.user_id}`}
                  >
                    <Heart className="w-4 h-4 mx-auto" fill="white" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <div className="w-20 h-20 rounded-full bg-[#E76F51]/10 flex items-center justify-center mx-auto mb-6">
            <Sparkles className="w-10 h-10 text-[#E76F51]" />
          </div>
          <h3 className="text-xl font-bold text-[#1C1917] mb-2" style={{ fontFamily: 'Syne, sans-serif' }}>
            No vibes yet
          </h3>
          <p className="text-[#57534E] mb-6">
            When someone likes your invite, they'll appear here
          </p>
          <Link to="/">
            <Button className="rounded-full bg-[#E76F51] hover:bg-[#D65D40]">
              Keep Discovering
            </Button>
          </Link>
        </div>
      )}
    </div>
  );
}
