import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { format, parseISO } from 'date-fns';
import { 
  ArrowLeft, 
  Send, 
  MoreVertical, 
  Flag, 
  Ban,
  MapPin,
  Clock,
  DollarSign,
  Check,
  Calendar
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../components/ui/alert-dialog';
import { useAuth } from '../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function ChatPage() {
  const { threadId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  
  const [thread, setThread] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newMessage, setNewMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [blockDialogOpen, setBlockDialogOpen] = useState(false);
  const [reportDialogOpen, setReportDialogOpen] = useState(false);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchMessages, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, [threadId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchData = async () => {
    try {
      const [threadRes, messagesRes] = await Promise.all([
        axios.get(`${API}/chat/threads/${threadId}`),
        axios.get(`${API}/chat/threads/${threadId}/messages`)
      ]);
      setThread(threadRes.data);
      setMessages(messagesRes.data);
    } catch (error) {
      toast.error('Failed to load chat');
      navigate('/chat');
    } finally {
      setLoading(false);
    }
  };

  const fetchMessages = async () => {
    try {
      const response = await axios.get(`${API}/chat/threads/${threadId}/messages`);
      setMessages(response.data);
    } catch (error) {
      // Silently fail on polling errors
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || sending) return;

    setSending(true);
    try {
      const response = await axios.post(`${API}/chat/threads/${threadId}/messages`, {
        content: newMessage.trim()
      });
      setMessages(prev => [...prev, response.data]);
      setNewMessage('');
      inputRef.current?.focus();
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to send message';
      toast.error(message);
    } finally {
      setSending(false);
    }
  };

  const handleConfirmDate = async () => {
    try {
      await axios.put(`${API}/chat/threads/${threadId}/confirm`, {
        is_confirmed: true
      });
      setThread(prev => ({ ...prev, is_confirmed: true }));
      toast.success('Date confirmed!');
      setConfirmDialogOpen(false);
    } catch (error) {
      toast.error('Failed to confirm date');
    }
  };

  const handleBlock = async () => {
    try {
      await axios.post(`${API}/block`, {
        blocked_user_id: thread.other_user_id
      });
      toast.success('User blocked');
      navigate('/chat');
    } catch (error) {
      toast.error('Failed to block user');
    }
  };

  const handleReport = async () => {
    try {
      await axios.post(`${API}/report`, {
        reported_user_id: thread.other_user_id,
        reason: 'inappropriate behavior'
      });
      toast.success('Report submitted');
      setReportDialogOpen(false);
    } catch (error) {
      toast.error('Failed to submit report');
    }
  };

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto h-[calc(100vh-200px)] flex flex-col">
        <div className="h-16 skeleton rounded-xl mb-4" />
        <div className="flex-1 space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className={`flex ${i % 2 === 0 ? '' : 'justify-end'}`}>
              <div className={`h-12 w-48 skeleton rounded-2xl`} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!thread) return null;

  return (
    <div className="max-w-2xl mx-auto h-[calc(100vh-180px)] md:h-[calc(100vh-140px)] flex flex-col animate-fadeIn">
      {/* Header */}
      <div className="bg-white rounded-2xl border border-stone-200 p-4 mb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate('/chat')}
            className="md:hidden"
            data-testid="back-btn"
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <Avatar className="w-10 h-10">
            <AvatarImage src={thread.other_user_photo} />
            <AvatarFallback className="bg-[#2A9D8F] text-white">
              {thread.other_user_name?.[0]?.toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div>
            <h2 className="font-semibold text-[#1C1917]">{thread.other_user_name}</h2>
            <p className="text-xs text-[#57534E] truncate max-w-[150px] sm:max-w-[250px]">
              {thread.date_post_title}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {thread.is_confirmed ? (
            <span className="text-xs px-3 py-1.5 rounded-full bg-[#2A9D8F]/10 text-[#2A9D8F] font-medium flex items-center gap-1">
              <Check className="w-3 h-3" />
              Confirmed
            </span>
          ) : (
            <Button
              size="sm"
              className="rounded-full bg-[#2A9D8F] hover:bg-[#238B7E] text-xs"
              onClick={() => setConfirmDialogOpen(true)}
              data-testid="confirm-date-btn"
            >
              <Check className="w-3 h-3 mr-1" />
              Confirm Date
            </Button>
          )}
          
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" data-testid="chat-menu-btn">
                <MoreVertical className="w-5 h-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => setReportDialogOpen(true)}>
                <Flag className="w-4 h-4 mr-2" />
                Report
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem 
                onClick={() => setBlockDialogOpen(true)}
                className="text-red-600"
              >
                <Ban className="w-4 h-4 mr-2" />
                Block User
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Date Details Card */}
      {!thread.is_confirmed && (
        <div className="bg-[#FDFCF8] rounded-xl border border-stone-200 p-4 mb-4">
          <p className="text-sm text-[#57534E] mb-3">
            Finalize the details for your date:
          </p>
          <div className="grid grid-cols-3 gap-3 text-sm">
            <div className="flex items-center gap-2 text-[#57534E]">
              <Calendar className="w-4 h-4 text-[#A8A29E]" />
              <span>Time TBD</span>
            </div>
            <div className="flex items-center gap-2 text-[#57534E]">
              <MapPin className="w-4 h-4 text-[#A8A29E]" />
              <span>Location TBD</span>
            </div>
            <div className="flex items-center gap-2 text-[#57534E]">
              <DollarSign className="w-4 h-4 text-[#A8A29E]" />
              <span>Split TBD</span>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4 px-1">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <p className="text-[#A8A29E] text-center">
              Start the conversation!<br />
              Say hi to {thread.other_user_name}
            </p>
          </div>
        ) : (
          messages.map((msg, idx) => {
            const isSent = msg.sender_id === user?.id;
            const showDate = idx === 0 || 
              format(parseISO(messages[idx - 1].created_at), 'yyyy-MM-dd') !== 
              format(parseISO(msg.created_at), 'yyyy-MM-dd');

            return (
              <React.Fragment key={msg.id}>
                {showDate && (
                  <div className="text-center text-xs text-[#A8A29E] py-2">
                    {format(parseISO(msg.created_at), 'EEEE, MMMM d')}
                  </div>
                )}
                <div className={`flex ${isSent ? 'justify-end' : 'justify-start'}`}>
                  <div 
                    className={`chat-bubble ${isSent ? 'chat-bubble-sent' : 'chat-bubble-received'}`}
                    data-testid={`message-${msg.id}`}
                  >
                    <p>{msg.content}</p>
                    <p className={`text-xs mt-1 ${isSent ? 'text-white/70' : 'text-[#A8A29E]'}`}>
                      {format(parseISO(msg.created_at), 'h:mm a')}
                    </p>
                  </div>
                </div>
              </React.Fragment>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSend} className="flex gap-2">
        <Input
          ref={inputRef}
          placeholder="Type a message..."
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          className="rounded-full bg-white"
          maxLength={1000}
          data-testid="message-input"
        />
        <Button
          type="submit"
          disabled={!newMessage.trim() || sending}
          className="btn-primary rounded-full px-6"
          data-testid="send-btn"
        >
          <Send className="w-4 h-4" />
        </Button>
      </form>

      {/* Confirm Dialog */}
      <Dialog open={confirmDialogOpen} onOpenChange={setConfirmDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Syne, sans-serif' }}>Confirm your date</DialogTitle>
            <DialogDescription>
              Mark this date as confirmed. This lets both of you know the plans are set!
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmDialogOpen(false)} className="rounded-full">
              Not yet
            </Button>
            <Button 
              onClick={handleConfirmDate}
              className="rounded-full bg-[#2A9D8F] hover:bg-[#238B7E]"
              data-testid="confirm-btn"
            >
              <Check className="w-4 h-4 mr-2" />
              Confirm Date
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Block Dialog */}
      <AlertDialog open={blockDialogOpen} onOpenChange={setBlockDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Block {thread.other_user_name}?</AlertDialogTitle>
            <AlertDialogDescription>
              They won't be able to see your profile or send you messages. This cannot be undone easily.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="rounded-full">Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleBlock}
              className="rounded-full bg-red-500 hover:bg-red-600"
              data-testid="confirm-block-btn"
            >
              Block
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Report Dialog */}
      <AlertDialog open={reportDialogOpen} onOpenChange={setReportDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Report {thread.other_user_name}?</AlertDialogTitle>
            <AlertDialogDescription>
              If you believe this user has violated our guidelines, please report them.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="rounded-full">Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleReport}
              className="rounded-full"
              data-testid="confirm-report-btn"
            >
              Submit Report
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
