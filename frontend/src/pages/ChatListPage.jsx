import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { format, parseISO } from 'date-fns';
import { MessageCircle, Heart } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Badge } from '../components/ui/badge';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function ChatListPage() {
  const [threads, setThreads] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchThreads();
  }, []);

  const fetchThreads = async () => {
    try {
      const response = await axios.get(`${API}/chat/threads`);
      setThreads(response.data);
    } catch (error) {
      toast.error('Failed to load chats');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="h-8 w-1/3 skeleton rounded mb-6" />
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white rounded-2xl border p-4 flex gap-4">
              <div className="w-14 h-14 skeleton rounded-full" />
              <div className="flex-1 space-y-2">
                <div className="h-5 w-1/3 skeleton rounded" />
                <div className="h-4 w-2/3 skeleton rounded" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto animate-fadeIn">
      <h1 
        className="text-2xl sm:text-3xl font-bold text-[#1C1917] mb-6"
        style={{ fontFamily: 'Syne, sans-serif' }}
      >
        Messages
      </h1>

      {threads.length > 0 ? (
        <div className="space-y-3">
          {threads.map((thread, idx) => (
            <Link
              key={thread.id}
              to={`/chat/${thread.id}`}
              className="block bg-white rounded-2xl border border-stone-200 p-4 hover:shadow-md transition-shadow animate-slideUp"
              style={{ animationDelay: `${idx * 0.05}s` }}
              data-testid={`chat-thread-${thread.id}`}
            >
              <div className="flex gap-4">
                <div className="relative">
                  <Avatar className="w-14 h-14">
                    <AvatarImage src={thread.other_user_photo} />
                    <AvatarFallback className="bg-[#2A9D8F] text-white text-lg">
                      {thread.other_user_name?.[0]?.toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  {thread.unread_count > 0 && (
                    <span className="absolute -top-1 -right-1 w-5 h-5 bg-[#E76F51] text-white text-xs rounded-full flex items-center justify-center">
                      {thread.unread_count}
                    </span>
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="font-semibold text-[#1C1917]">
                      {thread.other_user_name}
                    </h3>
                    {thread.last_message_at && (
                      <span className="text-xs text-[#A8A29E]">
                        {format(parseISO(thread.last_message_at), 'MMM d')}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-[#57534E] truncate">
                    {thread.last_message || 'Start the conversation!'}
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <Badge variant="outline" className="text-xs">
                      {thread.date_post_title}
                    </Badge>
                    {thread.is_confirmed && (
                      <Badge className="bg-[#2A9D8F] text-white text-xs">
                        Confirmed
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-state-icon">
            <MessageCircle className="w-10 h-10" />
          </div>
          <h3 className="text-xl font-bold text-[#1C1917] mb-2" style={{ fontFamily: 'Syne, sans-serif' }}>
            No messages yet
          </h3>
          <p className="text-[#57534E] mb-6">
            When you're matched with someone, your chat will appear here
          </p>
          <Link to="/">
            <button className="btn-primary rounded-full px-6 py-2.5 flex items-center gap-2 mx-auto">
              <Heart className="w-4 h-4" />
              Browse Dates
            </button>
          </Link>
        </div>
      )}
    </div>
  );
}
