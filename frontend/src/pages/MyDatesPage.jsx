import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { PlusCircle, Calendar, Users, Heart } from 'lucide-react';
import { Button } from '../components/ui/button';
import { DateCard } from '../components/DateCard';
import { useAuth } from '../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function MyDatesPage() {
  const { isAuthenticated } = useAuth();
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isAuthenticated) {
      fetchMyDates();
    }
  }, [isAuthenticated]);

  const fetchMyDates = async () => {
    try {
      const response = await axios.get(`${API}/my-dates`);
      setPosts(response.data);
    } catch (error) {
      toast.error('Failed to load your dates');
    } finally {
      setLoading(false);
    }
  };

  const handleLike = async (postId, isLiked) => {
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

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="h-10 w-1/3 skeleton rounded mb-6" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="date-card">
              <div className="aspect-[4/3] skeleton" />
              <div className="p-5 space-y-3">
                <div className="h-4 w-20 skeleton rounded" />
                <div className="h-6 w-3/4 skeleton rounded" />
                <div className="h-4 w-full skeleton rounded" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const openDates = posts.filter(p => p.status === 'OPEN');
  const selectedDates = posts.filter(p => p.status === 'SELECTED');
  const otherDates = posts.filter(p => !['OPEN', 'SELECTED'].includes(p.status));

  return (
    <div className="animate-fadeIn">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 
            className="text-2xl sm:text-3xl font-bold text-[#1C1917]"
            style={{ fontFamily: 'Syne, sans-serif' }}
          >
            My Dates
          </h1>
          <p className="text-[#57534E] mt-1">
            Manage the dates you've posted
          </p>
        </div>
        <Link to="/dates/new">
          <Button className="btn-primary rounded-full" data-testid="create-date-btn">
            <PlusCircle className="w-4 h-4 mr-2" />
            Post a Date
          </Button>
        </Link>
      </div>

      {posts.length > 0 ? (
        <div className="space-y-8">
          {/* Open Dates */}
          {openDates.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-2 h-2 rounded-full bg-[#2A9D8F]" />
                <h2 className="font-semibold text-lg text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
                  Open ({openDates.length})
                </h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {openDates.map((post, idx) => (
                  <div key={post.id} className="animate-slideUp" style={{ animationDelay: `${idx * 0.05}s` }}>
                    <DateCard post={post} onLike={handleLike} showStatus />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Selected Dates */}
          {selectedDates.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-2 h-2 rounded-full bg-[#E76F51]" />
                <h2 className="font-semibold text-lg text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
                  Selected ({selectedDates.length})
                </h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {selectedDates.map((post, idx) => (
                  <div key={post.id} className="animate-slideUp" style={{ animationDelay: `${idx * 0.05}s` }}>
                    <DateCard post={post} onLike={handleLike} showStatus />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Other Dates */}
          {otherDates.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-2 h-2 rounded-full bg-[#A8A29E]" />
                <h2 className="font-semibold text-lg text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
                  Past ({otherDates.length})
                </h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {otherDates.map((post, idx) => (
                  <div key={post.id} className="animate-slideUp" style={{ animationDelay: `${idx * 0.05}s` }}>
                    <DateCard post={post} onLike={handleLike} showStatus />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-state-icon">
            <Calendar className="w-10 h-10" />
          </div>
          <h3 className="text-xl font-bold text-[#1C1917] mb-2" style={{ fontFamily: 'Syne, sans-serif' }}>
            No dates yet
          </h3>
          <p className="text-[#57534E] mb-6">
            Post your first date idea and find someone to join you!
          </p>
          <Link to="/dates/new">
            <Button className="btn-primary rounded-full px-6" data-testid="create-first-date-btn">
              <PlusCircle className="w-4 h-4 mr-2" />
              Post a Date
            </Button>
          </Link>
        </div>
      )}
    </div>
  );
}
