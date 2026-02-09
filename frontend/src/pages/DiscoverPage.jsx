import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { 
  Heart, X, MapPin, Filter, Sparkles, Clock, SlidersHorizontal,
  Coffee, Utensils, Mountain, Palette, Music, Dumbbell
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Slider } from '../components/ui/slider';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '../components/ui/sheet';
import { useAuth } from '../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TAG_ICONS = {
  coffee: Coffee,
  dinner: Utensils,
  brunch: Utensils,
  outdoors: Mountain,
  hiking: Mountain,
  museum: Palette,
  art: Palette,
  music: Music,
  fitness: Dumbbell,
};

const QUICK_TAGS = ['coffee', 'dinner', 'outdoors', 'museum', 'music', 'adventure', 'chill', 'active'];

export default function DiscoverPage() {
  const { profile } = useAuth();
  const [invites, setInvites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isLiking, setIsLiking] = useState(false);
  const [isPassing, setIsPassing] = useState(false);
  const [filterOpen, setFilterOpen] = useState(false);
  const [swipeDirection, setSwipeDirection] = useState(null); // 'left' or 'right'
  
  // Filters
  const [filters, setFilters] = useState({
    interested_in: profile?.interested_in || [],
    max_distance: profile?.distance_preference || 50,
    tags: [],
    sort_by: 'recommended'
  });
  const [activeQuickTag, setActiveQuickTag] = useState(null);

  const fetchInvites = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.interested_in.length > 0) {
        params.append('interested_in', filters.interested_in.join(','));
      }
      if (filters.max_distance) {
        params.append('max_distance', filters.max_distance);
      }
      if (activeQuickTag) {
        params.append('tags', activeQuickTag);
      } else if (filters.tags.length > 0) {
        params.append('tags', filters.tags.join(','));
      }
      params.append('sort_by', filters.sort_by);
      params.append('limit', 50);

      const response = await axios.get(`${API}/discover?${params.toString()}`);
      setInvites(response.data.invites);
      setCurrentIndex(0);
    } catch (error) {
      console.error('Failed to fetch invites:', error);
    } finally {
      setLoading(false);
    }
  }, [filters, activeQuickTag]);

  useEffect(() => {
    fetchInvites();
  }, [fetchInvites]);

  const handleLike = async () => {
    if (isLiking || currentIndex >= invites.length) return;
    
    const invite = invites[currentIndex];
    setIsLiking(true);
    setSwipeDirection('right');
    
    try {
      const response = await axios.post(`${API}/like/${invite.user_id}`);
      
      if (response.data.is_match) {
        toast.success(`It is a match with ${invite.first_name}!`, {
          description: 'Go to Plans to start chatting!'
        });
      } else {
        toast.success(`Liked ${invite.first_name}'s invite!`);
      }
      
      // Wait for animation to complete
      setTimeout(() => {
        setCurrentIndex(prev => prev + 1);
        setSwipeDirection(null);
      }, 300);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to like');
      setSwipeDirection(null);
    } finally {
      setIsLiking(false);
    }
  };

  const handlePass = async () => {
    if (isPassing || currentIndex >= invites.length) return;
    
    const invite = invites[currentIndex];
    setIsPassing(true);
    setSwipeDirection('left');
    
    try {
      // Record the pass so this profile doesn't show again
      await axios.post(`${API}/pass/${invite.user_id}`);
      toast('Passed', { duration: 1500 });
    } catch (error) {
      // Still move to next even if pass fails
      console.error('Pass failed:', error);
    }
    
    // Wait for animation to complete
    setTimeout(() => {
      setCurrentIndex(prev => prev + 1);
      setSwipeDirection(null);
      setIsPassing(false);
    }, 300);
  };

  const toggleQuickTag = (tag) => {
    setActiveQuickTag(prev => prev === tag ? null : tag);
  };

  const currentInvite = invites[currentIndex];
  const hasMore = currentIndex < invites.length;

  return (
    <div className="min-h-screen bg-[#FDFCF8]">
      {/* Header */}
      <div className="sticky top-0 z-40 bg-[#FDFCF8]/95 backdrop-blur-lg border-b border-stone-200/50">
        <div className="px-4 py-3">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-2xl font-bold text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
              Discover
            </h1>
            
            {/* Filter Button */}
            <Sheet open={filterOpen} onOpenChange={setFilterOpen}>
              <SheetTrigger asChild>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="rounded-full"
                  data-testid="filter-btn"
                >
                  <SlidersHorizontal className="w-4 h-4 mr-2" />
                  Filters
                </Button>
              </SheetTrigger>
              <SheetContent side="bottom" className="h-[70vh] rounded-t-3xl">
                <SheetHeader>
                  <SheetTitle style={{ fontFamily: 'Syne, sans-serif' }}>Filters</SheetTitle>
                  <SheetDescription>Find your perfect match</SheetDescription>
                </SheetHeader>
                
                <div className="py-6 space-y-8">
                  {/* Interested In */}
                  <div>
                    <label className="text-sm font-medium text-[#1C1917] mb-3 block">
                      Show me
                    </label>
                    <div className="flex gap-3">
                      {['male', 'female'].map(g => (
                        <button
                          key={g}
                          onClick={() => {
                            setFilters(prev => ({
                              ...prev,
                              interested_in: prev.interested_in.includes(g)
                                ? prev.interested_in.filter(x => x !== g)
                                : [...prev.interested_in, g]
                            }));
                          }}
                          className={`flex-1 py-3 rounded-xl border-2 font-medium transition-all ${
                            filters.interested_in.includes(g)
                              ? 'border-[#E76F51] bg-[#E76F51]/5 text-[#E76F51]'
                              : 'border-stone-200 text-[#57534E]'
                          }`}
                        >
                          {g === 'male' ? 'Men' : 'Women'}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Distance */}
                  <div>
                    <label className="text-sm font-medium text-[#1C1917] mb-3 block">
                      Maximum distance: {filters.max_distance} miles
                    </label>
                    <Slider
                      value={[filters.max_distance]}
                      onValueChange={(v) => setFilters(prev => ({ ...prev, max_distance: v[0] }))}
                      min={1}
                      max={100}
                      step={1}
                    />
                  </div>

                  {/* Sort */}
                  <div>
                    <label className="text-sm font-medium text-[#1C1917] mb-3 block">
                      Sort by
                    </label>
                    <div className="flex gap-3">
                      {[
                        { value: 'recommended', label: 'For You', icon: Sparkles },
                        { value: 'new', label: 'New', icon: Clock }
                      ].map(opt => (
                        <button
                          key={opt.value}
                          onClick={() => setFilters(prev => ({ ...prev, sort_by: opt.value }))}
                          className={`flex-1 py-3 rounded-xl border-2 font-medium flex items-center justify-center gap-2 transition-all ${
                            filters.sort_by === opt.value
                              ? 'border-[#2A9D8F] bg-[#2A9D8F]/5 text-[#2A9D8F]'
                              : 'border-stone-200 text-[#57534E]'
                          }`}
                        >
                          <opt.icon className="w-4 h-4" />
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <Button 
                    onClick={() => { setFilterOpen(false); fetchInvites(); }}
                    className="w-full rounded-full bg-[#E76F51] hover:bg-[#D65D40]"
                  >
                    Apply Filters
                  </Button>
                </div>
              </SheetContent>
            </Sheet>
          </div>

          {/* Quick Tags */}
          <div className="flex gap-2 overflow-x-auto pb-2 -mx-4 px-4 scrollbar-hide">
            {QUICK_TAGS.map(tag => {
              const Icon = TAG_ICONS[tag] || Sparkles;
              return (
                <button
                  key={tag}
                  onClick={() => toggleQuickTag(tag)}
                  className={`flex items-center gap-1.5 px-4 py-2 rounded-full border whitespace-nowrap transition-all ${
                    activeQuickTag === tag
                      ? 'bg-[#E76F51] text-white border-[#E76F51]'
                      : 'bg-white border-stone-200 text-[#57534E]'
                  }`}
                  data-testid={`quick-tag-${tag}`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="capitalize text-sm font-medium">{tag}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Card Stack */}
      <div className="px-4 pt-4 pb-8">
        {loading ? (
          <div className="aspect-[3/4] max-w-sm mx-auto bg-white rounded-3xl shadow-lg overflow-hidden animate-pulse">
            <div className="h-2/3 bg-stone-200" />
            <div className="p-5 space-y-3">
              <div className="h-6 bg-stone-200 rounded w-1/3" />
              <div className="h-4 bg-stone-200 rounded w-2/3" />
              <div className="h-4 bg-stone-200 rounded w-1/2" />
            </div>
          </div>
        ) : hasMore && currentInvite ? (
          <div className="relative max-w-sm mx-auto">
            {/* Main Card */}
            <div 
              className={`bg-white rounded-3xl shadow-xl overflow-hidden transition-all duration-300 ${
                swipeDirection === 'left' 
                  ? 'transform -translate-x-full rotate-[-15deg] opacity-0' 
                  : swipeDirection === 'right' 
                  ? 'transform translate-x-full rotate-[15deg] opacity-0'
                  : 'animate-scaleIn'
              }`}
              data-testid={`invite-card-${currentInvite.user_id}`}
            >
              {/* Photo */}
              <div className="relative aspect-square">
                <img 
                  src={currentInvite.main_photo} 
                  alt={currentInvite.first_name}
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
                
                {/* Name & Location */}
                <div className="absolute bottom-4 left-4 right-4 text-white">
                  <h2 className="text-2xl font-bold" style={{ fontFamily: 'Syne, sans-serif' }}>
                    {currentInvite.first_name}
                  </h2>
                  <div className="flex items-center gap-1 text-white/80 text-sm mt-1">
                    <MapPin className="w-4 h-4" />
                    <span>{currentInvite.city}</span>
                  </div>
                </div>
              </div>

              {/* Date Idea */}
              <div className="p-5">
                {/* Tags */}
                <div className="flex flex-wrap gap-2 mb-3">
                  {currentInvite.first_date_idea?.tags?.slice(0, 3).map((tag, idx) => (
                    <span 
                      key={idx}
                      className={`px-3 py-1 rounded-full text-xs font-medium ${
                        idx === 0 
                          ? 'bg-[#E76F51]/10 text-[#E76F51]' 
                          : 'bg-[#2A9D8F]/10 text-[#2A9D8F]'
                      }`}
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                {/* Title */}
                <h3 className="font-bold text-lg text-[#1C1917] mb-2" style={{ fontFamily: 'Syne, sans-serif' }}>
                  {currentInvite.first_date_idea?.title || 'First Date Idea'}
                </h3>

                {/* Description */}
                <p className="text-[#57534E] text-sm leading-relaxed">
                  {currentInvite.first_date_idea?.description || 'No description yet'}
                </p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-center gap-6 mt-6">
              <button
                onClick={handlePass}
                disabled={isPassing}
                className={`w-16 h-16 rounded-full bg-white shadow-lg flex items-center justify-center transition-all border border-stone-200 ${
                  isPassing 
                    ? 'text-red-500 scale-110 shadow-xl' 
                    : 'text-[#A8A29E] hover:text-red-500 hover:shadow-xl'
                } disabled:opacity-70`}
                data-testid="pass-btn"
              >
                <X className="w-8 h-8" />
              </button>
              
              <button
                onClick={handleLike}
                disabled={isLiking}
                className={`w-20 h-20 rounded-full bg-gradient-to-br from-[#E76F51] to-[#E9C46A] shadow-lg flex items-center justify-center text-white transition-all ${
                  isLiking 
                    ? 'scale-110 shadow-xl' 
                    : 'hover:shadow-xl'
                } disabled:opacity-70`}
                data-testid="like-btn"
              >
                <Heart className="w-10 h-10" fill="white" />
              </button>
            </div>
          </div>
        ) : (
          <div className="max-w-sm mx-auto text-center py-20">
            <div className="w-20 h-20 rounded-full bg-stone-100 flex items-center justify-center mx-auto mb-6">
              <Heart className="w-10 h-10 text-[#A8A29E]" />
            </div>
            <h3 className="text-xl font-bold text-[#1C1917] mb-2" style={{ fontFamily: 'Syne, sans-serif' }}>
              No more invites
            </h3>
            <p className="text-[#57534E] mb-6">
              Check back later or adjust your filters
            </p>
            <Button 
              onClick={fetchInvites}
              variant="outline"
              className="rounded-full"
            >
              Refresh
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
