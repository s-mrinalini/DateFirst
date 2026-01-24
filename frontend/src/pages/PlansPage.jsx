import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { format, parseISO } from 'date-fns';
import { MessageCircle, Heart, Sparkles, Check } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function PlansPage() {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await axios.get(`${API}/plans`);
      setPlans(response.data.plans);
    } catch (error) {
      toast.error('Failed to load plans');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-4">
        <div className="h-8 bg-stone-200 rounded w-1/3 mb-6 animate-pulse" />
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="bg-white rounded-2xl p-4 shadow animate-pulse">
              <div className="flex gap-4">
                <div className="w-16 h-16 rounded-full bg-stone-200" />
                <div className="flex-1 space-y-2">
                  <div className="h-5 bg-stone-200 rounded w-1/3" />
                  <div className="h-4 bg-stone-200 rounded w-2/3" />
                </div>
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
          Plans
        </h1>
        <p className="text-[#57534E] text-sm mt-1">
          Your matches and conversations
        </p>
      </div>

      {plans.length > 0 ? (
        <div className="space-y-3">
          {plans.map((plan, idx) => (
            <Link
              key={plan.thread_id}
              to={`/chat/${plan.thread_id}`}
              className="block bg-white rounded-2xl p-4 shadow-sm hover:shadow-md transition-shadow animate-slideUp"
              style={{ animationDelay: `${idx * 0.05}s` }}
              data-testid={`plan-${plan.thread_id}`}
            >
              <div className="flex gap-4">
                <Avatar className="w-16 h-16">
                  <AvatarImage src={plan.other_user_photo} />
                  <AvatarFallback className="bg-[#2A9D8F] text-white text-lg">
                    {plan.other_user_name?.[0]?.toUpperCase()}
                  </AvatarFallback>
                </Avatar>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="font-bold text-[#1C1917]">{plan.other_user_name}</h3>
                    {plan.last_message_at && (
                      <span className="text-xs text-[#A8A29E]">
                        {format(parseISO(plan.last_message_at), 'MMM d')}
                      </span>
                    )}
                  </div>

                  {/* Matched On */}
                  <p className="text-xs text-[#E76F51] font-medium mb-1 truncate">
                    📍 {plan.matched_on_idea?.title || 'Date Idea'}
                  </p>

                  {/* Last Message */}
                  <p className="text-sm text-[#57534E] truncate">
                    {plan.last_message || 'Start the conversation!'}
                  </p>

                  {/* Plan Status */}
                  {plan.date_plan?.is_confirmed && (
                    <div className="flex items-center gap-1 mt-2 text-xs text-[#2A9D8F]">
                      <Check className="w-3 h-3" />
                      <span>Date confirmed!</span>
                    </div>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <div className="w-20 h-20 rounded-full bg-[#2A9D8F]/10 flex items-center justify-center mx-auto mb-6">
            <Heart className="w-10 h-10 text-[#2A9D8F]" />
          </div>
          <h3 className="text-xl font-bold text-[#1C1917] mb-2" style={{ fontFamily: 'Syne, sans-serif' }}>
            No matches yet
          </h3>
          <p className="text-[#57534E] mb-6">
            When you match with someone, you'll chat here
          </p>
          <Link to="/">
            <Button className="rounded-full bg-[#E76F51] hover:bg-[#D65D40]">
              Start Discovering
            </Button>
          </Link>
        </div>
      )}
    </div>
  );
}
