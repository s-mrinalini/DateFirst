import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { 
  Search, 
  Filter, 
  MapPin, 
  Calendar,
  TrendingUp,
  Clock,
  Coffee,
  Utensils,
  Mountain,
  Palette,
  Music,
  Sparkles,
  Heart,
  PlusCircle
} from 'lucide-react';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { DateCard } from '../components/DateCard';
import { useAuth } from '../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TAG_OPTIONS = [
  { value: 'coffee', label: 'Coffee', icon: Coffee },
  { value: 'dinner', label: 'Dinner', icon: Utensils },
  { value: 'outdoors', label: 'Outdoors', icon: Mountain },
  { value: 'museum', label: 'Museum', icon: Palette },
  { value: 'music', label: 'Music', icon: Music },
  { value: 'hiking', label: 'Hiking', icon: Mountain },
];

const WHO_PAYS_OPTIONS = [
  { value: 'all', label: 'Any' },
  { value: 'i_pay', label: 'They pay' },
  { value: 'split', label: 'Split' },
  { value: 'you_pay', label: 'You pay' },
  { value: 'decide_later', label: 'Decide later' },
];

const TIME_OPTIONS = [
  { value: 'all', label: 'Any time' },
  { value: 'today', label: 'Today' },
  { value: 'this_week', label: 'This week' },
];

const SORT_OPTIONS = [
  { value: 'newest', label: 'Newest', icon: Sparkles },
  { value: 'soonest', label: 'Soonest', icon: Clock },
  { value: 'popular', label: 'Most liked', icon: TrendingUp },
];

export default function HomePage() {
  const { isAuthenticated } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  
  // Filters
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [city, setCity] = useState(searchParams.get('city') || '');
  const [selectedTags, setSelectedTags] = useState(
    searchParams.get('tags')?.split(',').filter(Boolean) || []
  );
  const [whoPays, setWhoPays] = useState(searchParams.get('who_pays') || 'all');
  const [timeFilter, setTimeFilter] = useState(searchParams.get('time') || 'all');
  const [sortBy, setSortBy] = useState(searchParams.get('sort') || 'newest');

  const fetchPosts = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (city) params.append('city', city);
      if (selectedTags.length > 0) params.append('tags', selectedTags.join(','));
      if (whoPays !== 'all') params.append('who_pays', whoPays);
      if (timeFilter !== 'all') params.append('time_filter', timeFilter);
      params.append('sort_by', sortBy);
      params.append('page', page);
      params.append('limit', 20);

      const response = await axios.get(`${API}/dates?${params.toString()}`);
      setPosts(response.data.posts);
      setTotal(response.data.total);
      setPages(response.data.pages);
    } catch (error) {
      console.error('Failed to fetch dates:', error);
      toast.error('Failed to load dates');
    } finally {
      setLoading(false);
    }
  }, [search, city, selectedTags, whoPays, timeFilter, sortBy, page]);

  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]);

  // Update URL params
  useEffect(() => {
    const params = new URLSearchParams();
    if (search) params.set('search', search);
    if (city) params.set('city', city);
    if (selectedTags.length > 0) params.set('tags', selectedTags.join(','));
    if (whoPays !== 'all') params.set('who_pays', whoPays);
    if (timeFilter !== 'all') params.set('time', timeFilter);
    if (sortBy !== 'newest') params.set('sort', sortBy);
    setSearchParams(params, { replace: true });
  }, [search, city, selectedTags, whoPays, timeFilter, sortBy, setSearchParams]);

  const handleLike = async (postId, isLiked) => {
    if (!isAuthenticated) {
      toast.error('Please sign in to like dates');
      return;
    }

    try {
      if (isLiked) {
        await axios.delete(`${API}/dates/${postId}/like`);
      } else {
        await axios.post(`${API}/dates/${postId}/like`);
      }
      
      setPosts(posts.map(post => {
        if (post.id === postId) {
          return {
            ...post,
            is_liked: !isLiked,
            like_count: isLiked ? post.like_count - 1 : post.like_count + 1
          };
        }
        return post;
      }));
    } catch (error) {
      toast.error('Failed to update like');
    }
  };

  const toggleTag = (tag) => {
    setSelectedTags(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
    setPage(1);
  };

  const clearFilters = () => {
    setSearch('');
    setCity('');
    setSelectedTags([]);
    setWhoPays('all');
    setTimeFilter('all');
    setSortBy('newest');
    setPage(1);
  };

  const hasFilters = search || city || selectedTags.length > 0 || whoPays !== 'all' || timeFilter !== 'all';

  return (
    <div className="animate-fadeIn">
      {/* Hero Section */}
      <div className="mb-8">
        <h1 
          className="text-3xl sm:text-4xl lg:text-5xl font-bold text-[#1C1917] mb-3"
          style={{ fontFamily: 'Syne, sans-serif' }}
        >
          Find your next adventure
        </h1>
        <p className="text-base lg:text-lg text-[#57534E] max-w-2xl">
          Browse date ideas posted by people near you. Apply to the ones that excite you.
        </p>
      </div>

      {/* Search & Filters */}
      <div className="bg-white rounded-2xl border border-stone-200 p-4 mb-6 shadow-sm">
        <div className="flex flex-col sm:flex-row gap-3 mb-4">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#A8A29E]" />
            <Input
              placeholder="Search dates..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="pl-10 rounded-xl border-stone-200"
              data-testid="search-input"
            />
          </div>

          {/* City */}
          <div className="relative sm:w-48">
            <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#A8A29E]" />
            <Input
              placeholder="City"
              value={city}
              onChange={(e) => { setCity(e.target.value); setPage(1); }}
              className="pl-10 rounded-xl border-stone-200"
              data-testid="city-input"
            />
          </div>

          {/* Time Filter */}
          <Select value={timeFilter} onValueChange={(v) => { setTimeFilter(v); setPage(1); }}>
            <SelectTrigger className="sm:w-40 rounded-xl" data-testid="time-filter">
              <Calendar className="w-4 h-4 mr-2 text-[#A8A29E]" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {TIME_OPTIONS.map(opt => (
                <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* Who Pays */}
          <Select value={whoPays} onValueChange={(v) => { setWhoPays(v); setPage(1); }}>
            <SelectTrigger className="sm:w-40 rounded-xl" data-testid="who-pays-filter">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {WHO_PAYS_OPTIONS.map(opt => (
                <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-2">
          {TAG_OPTIONS.map(({ value, label, icon: Icon }) => (
            <button
              key={value}
              onClick={() => toggleTag(value)}
              className={`filter-chip flex items-center gap-2 ${
                selectedTags.includes(value) ? 'active' : ''
              }`}
              data-testid={`tag-${value}`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>

        {/* Sort & Clear */}
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-stone-100">
          <div className="flex items-center gap-2">
            <span className="text-sm text-[#57534E]">Sort by:</span>
            <div className="flex gap-1">
              {SORT_OPTIONS.map(({ value, label, icon: Icon }) => (
                <button
                  key={value}
                  onClick={() => { setSortBy(value); setPage(1); }}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium flex items-center gap-1.5 transition-colors ${
                    sortBy === value 
                      ? 'bg-[#1C1917] text-white' 
                      : 'text-[#57534E] hover:bg-stone-100'
                  }`}
                  data-testid={`sort-${value}`}
                >
                  <Icon className="w-4 h-4" />
                  {label}
                </button>
              ))}
            </div>
          </div>

          {hasFilters && (
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={clearFilters}
              className="text-[#E76F51]"
              data-testid="clear-filters"
            >
              Clear filters
            </Button>
          )}
        </div>
      </div>

      {/* Results Count */}
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-[#57534E]">
          {total} date{total !== 1 ? 's' : ''} found
        </p>
      </div>

      {/* Date Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="date-card">
              <div className="aspect-[4/3] skeleton" />
              <div className="p-5 space-y-3">
                <div className="h-4 w-20 skeleton rounded" />
                <div className="h-6 w-3/4 skeleton rounded" />
                <div className="h-4 w-full skeleton rounded" />
                <div className="h-4 w-2/3 skeleton rounded" />
              </div>
            </div>
          ))}
        </div>
      ) : posts.length > 0 ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {posts.map((post, idx) => (
              <div 
                key={post.id} 
                className="animate-slideUp"
                style={{ animationDelay: `${idx * 0.05}s` }}
              >
                <DateCard post={post} onLike={handleLike} />
              </div>
            ))}
          </div>

          {/* Pagination */}
          {pages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-8">
              <Button
                variant="outline"
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="rounded-full"
              >
                Previous
              </Button>
              <span className="px-4 text-sm text-[#57534E]">
                Page {page} of {pages}
              </span>
              <Button
                variant="outline"
                onClick={() => setPage(p => Math.min(pages, p + 1))}
                disabled={page === pages}
                className="rounded-full"
              >
                Next
              </Button>
            </div>
          )}
        </>
      ) : (
        <div className="empty-state">
          <div className="empty-state-icon">
            <Heart className="w-10 h-10" />
          </div>
          <h3 className="text-xl font-bold text-[#1C1917] mb-2" style={{ fontFamily: 'Syne, sans-serif' }}>
            No dates found
          </h3>
          <p className="text-[#57534E] mb-6">
            {hasFilters 
              ? "Try adjusting your filters to find more dates"
              : "Be the first to post a date idea!"
            }
          </p>
          {isAuthenticated ? (
            <Link to="/dates/new">
              <Button className="btn-primary rounded-full px-6" data-testid="create-first-date-btn">
                <PlusCircle className="w-4 h-4 mr-2" />
                Post a Date
              </Button>
            </Link>
          ) : (
            <Link to="/auth">
              <Button className="btn-primary rounded-full px-6" data-testid="signin-to-post-btn">
                Sign in to post
              </Button>
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
