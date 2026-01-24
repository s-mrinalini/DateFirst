import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { format, parseISO } from 'date-fns';
import { 
  ArrowLeft, Send, MoreVertical, Flag, Ban, Calendar, MapPin,
  DollarSign, Check, ChevronDown, ChevronUp
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
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '../components/ui/collapsible';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { useAuth } from '../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function ChatPage() {
  const { threadId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  
  const [thread, setThread] = useState(null);
  const [otherUser, setOtherUser] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newMessage, setNewMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [planOpen, setPlanOpen] = useState(false);
  const [datePlan, setDatePlan] = useState({
    proposed_datetime: '',
    proposed_location: '',
    who_pays: ''
  });

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchMessages, 5000);
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
        axios.get(`${API}/chat/${threadId}`),
        axios.get(`${API}/chat/${threadId}/messages`)
      ]);
      setThread(threadRes.data.thread);
      setOtherUser(threadRes.data.other_user);
      setMessages(messagesRes.data.messages);
      
      if (threadRes.data.thread?.date_plan) {
        setDatePlan({
          proposed_datetime: threadRes.data.thread.date_plan.proposed_datetime || '',
          proposed_location: threadRes.data.thread.date_plan.proposed_location || '',
          who_pays: threadRes.data.thread.date_plan.who_pays || ''
        });
      }
    } catch (error) {
      toast.error('Failed to load chat');
      navigate('/plans');
    } finally {
      setLoading(false);
    }
  };

  const fetchMessages = async () => {
    try {
      const response = await axios.get(`${API}/chat/${threadId}/messages`);
      setMessages(response.data.messages);
    } catch (error) {}
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || sending) return;

    setSending(true);
    try {
      const response = await axios.post(`${API}/chat/${threadId}/messages`, {
        content: newMessage.trim()
      });
      setMessages(prev => [...prev, response.data]);
      setNewMessage('');
      inputRef.current?.focus();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send');
    } finally {
      setSending(false);
    }
  };

  const handleUpdatePlan = async (field, value) => {
    try {
      const data = { [field]: value };
      await axios.put(`${API}/chat/${threadId}/plan`, data);
      setDatePlan(prev => ({ ...prev, [field]: value }));
      toast.success('Plan updated!');
    } catch (error) {
      toast.error('Failed to update');
    }
  };

  const handleConfirmDate = async () => {
    try {
      await axios.put(`${API}/chat/${threadId}/plan`, { is_confirmed: true });
      setThread(prev => ({
        ...prev,
        date_plan: { ...prev.date_plan, is_confirmed: true }
      }));
      toast.success('Date confirmed! 🎉');
    } catch (error) {
      toast.error('Failed to confirm');
    }
  };

  const handleBlock = async () => {
    try {
      await axios.post(`${API}/block`, { blocked_user_id: otherUser.user_id });
      toast.success('User blocked');
      navigate('/plans');
    } catch (error) {
      toast.error('Failed to block');
    }
  };

  const handleReport = async () => {
    try {
      await axios.post(`${API}/report`, {
        reported_user_id: otherUser.user_id,
        reason: 'inappropriate'
      });
      toast.success('Report submitted');
    } catch (error) {
      toast.error('Failed to report');
    }
  };

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="animate-pulse text-[#E76F51]">Loading...</div>
      </div>
    );
  }

  if (!thread || !otherUser) return null;

  return (
    <div className="h-screen flex flex-col bg-[#FDFCF8]">
      {/* Header */}
      <div className="bg-white border-b border-stone-200 px-4 py-3 flex items-center gap-3">
        <button 
          onClick={() => navigate('/plans')}
          className="p-2 -ml-2 hover:bg-stone-100 rounded-full"
          data-testid="back-btn"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>

        <Avatar className="w-10 h-10">
          <AvatarImage src={otherUser.main_photo} />
          <AvatarFallback className="bg-[#2A9D8F] text-white">
            {otherUser.first_name?.[0]}
          </AvatarFallback>
        </Avatar>

        <div className="flex-1 min-w-0">
          <h2 className="font-bold text-[#1C1917]">{otherUser.first_name}</h2>
          <p className="text-xs text-[#57534E] truncate">
            {thread.matched_on_idea?.title}
          </p>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="p-2 hover:bg-stone-100 rounded-full" data-testid="chat-menu">
              <MoreVertical className="w-5 h-5 text-[#57534E]" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={handleReport}>
              <Flag className="w-4 h-4 mr-2" /> Report
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleBlock} className="text-red-600">
              <Ban className="w-4 h-4 mr-2" /> Block
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Matched On Banner */}
      <div className="bg-gradient-to-r from-[#E76F51]/10 to-[#E9C46A]/10 px-4 py-3 border-b border-stone-200">
        <p className="text-xs text-[#57534E] mb-1">Matched on their invite:</p>
        <p className="font-medium text-[#1C1917]">{thread.matched_on_idea?.title}</p>
        <p className="text-sm text-[#57534E] mt-1">{thread.matched_on_idea?.description}</p>
      </div>

      {/* Plan the Date Section */}
      <Collapsible open={planOpen} onOpenChange={setPlanOpen}>
        <CollapsibleTrigger asChild>
          <button className="w-full bg-white border-b border-stone-200 px-4 py-3 flex items-center justify-between text-left">
            <div className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-[#2A9D8F]" />
              <span className="font-medium text-[#1C1917]">Plan the date</span>
              {thread.date_plan?.is_confirmed && (
                <span className="text-xs bg-[#2A9D8F] text-white px-2 py-0.5 rounded-full">
                  Confirmed!
                </span>
              )}
            </div>
            {planOpen ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="bg-white border-b border-stone-200 p-4 space-y-4">
            <div>
              <label className="text-xs text-[#57534E] mb-1 block">When?</label>
              <Input
                type="datetime-local"
                value={datePlan.proposed_datetime || ''}
                onChange={(e) => handleUpdatePlan('proposed_datetime', e.target.value)}
                className="rounded-xl"
                data-testid="plan-datetime"
              />
            </div>

            <div>
              <label className="text-xs text-[#57534E] mb-1 block">Where?</label>
              <Input
                placeholder="Meeting spot..."
                value={datePlan.proposed_location || ''}
                onChange={(e) => handleUpdatePlan('proposed_location', e.target.value)}
                onBlur={(e) => handleUpdatePlan('proposed_location', e.target.value)}
                className="rounded-xl"
                data-testid="plan-location"
              />
            </div>

            <div>
              <label className="text-xs text-[#57534E] mb-1 block">Who pays?</label>
              <Select 
                value={datePlan.who_pays || ''} 
                onValueChange={(v) => handleUpdatePlan('who_pays', v)}
              >
                <SelectTrigger className="rounded-xl" data-testid="plan-who-pays">
                  <SelectValue placeholder="Decide..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="i_pay">I'll pay</SelectItem>
                  <SelectItem value="split">Split</SelectItem>
                  <SelectItem value="you_pay">They pay</SelectItem>
                  <SelectItem value="decide_later">Decide later</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {!thread.date_plan?.is_confirmed && (
              <Button
                onClick={handleConfirmDate}
                className="w-full rounded-full bg-[#2A9D8F] hover:bg-[#238B7E]"
                data-testid="confirm-date-btn"
              >
                <Check className="w-4 h-4 mr-2" />
                Confirm Date
              </Button>
            )}
          </div>
        </CollapsibleContent>
      </Collapsible>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-8 text-[#A8A29E]">
            Say hi to {otherUser.first_name}!
          </div>
        ) : (
          messages.map((msg) => {
            const isSent = msg.sender_id === user?.id;
            return (
              <div 
                key={msg.id}
                className={`flex ${isSent ? 'justify-end' : 'justify-start'}`}
              >
                <div 
                  className={`max-w-[75%] px-4 py-2.5 rounded-2xl ${
                    isSent 
                      ? 'bg-[#E76F51] text-white rounded-br-md' 
                      : 'bg-white text-[#1C1917] shadow-sm rounded-bl-md'
                  }`}
                  data-testid={`msg-${msg.id}`}
                >
                  <p>{msg.content}</p>
                  <p className={`text-xs mt-1 ${isSent ? 'text-white/70' : 'text-[#A8A29E]'}`}>
                    {format(parseISO(msg.created_at), 'h:mm a')}
                  </p>
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form 
        onSubmit={handleSend}
        className="bg-white border-t border-stone-200 p-4 flex gap-2"
      >
        <Input
          ref={inputRef}
          placeholder="Message..."
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          className="rounded-full"
          maxLength={1000}
          data-testid="message-input"
        />
        <Button
          type="submit"
          disabled={!newMessage.trim() || sending}
          className="rounded-full bg-[#E76F51] hover:bg-[#D65D40] px-4"
          data-testid="send-btn"
        >
          <Send className="w-5 h-5" />
        </Button>
      </form>
    </div>
  );
}
