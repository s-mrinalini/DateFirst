import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { format, parseISO } from 'date-fns';
import { FileText, MapPin, Calendar, Clock, Heart, X } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
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

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const getStatusColor = (status) => {
  switch (status) {
    case 'pending': return 'bg-[#E9C46A]/20 text-[#B8860B]';
    case 'accepted': return 'bg-[#2A9D8F]/20 text-[#2A9D8F]';
    case 'declined': return 'bg-stone-100 text-[#57534E]';
    case 'withdrawn': return 'bg-stone-100 text-[#A8A29E]';
    default: return 'bg-stone-100 text-[#57534E]';
  }
};

export default function MyApplicationsPage() {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [withdrawId, setWithdrawId] = useState(null);

  useEffect(() => {
    fetchApplications();
  }, []);

  const fetchApplications = async () => {
    try {
      const response = await axios.get(`${API}/my-applications`);
      setApplications(response.data);
    } catch (error) {
      toast.error('Failed to load applications');
    } finally {
      setLoading(false);
    }
  };

  const handleWithdraw = async () => {
    if (!withdrawId) return;
    
    try {
      await axios.delete(`${API}/applications/${withdrawId}`);
      setApplications(prev => prev.filter(app => app.id !== withdrawId));
      toast.success('Application withdrawn');
    } catch (error) {
      toast.error('Failed to withdraw application');
    } finally {
      setWithdrawId(null);
    }
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="h-10 w-1/3 skeleton rounded mb-6" />
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="bg-white rounded-2xl border p-5">
              <div className="flex gap-4">
                <div className="h-20 w-20 skeleton rounded-xl" />
                <div className="flex-1 space-y-2">
                  <div className="h-5 w-2/3 skeleton rounded" />
                  <div className="h-4 w-1/3 skeleton rounded" />
                  <div className="h-4 w-1/2 skeleton rounded" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const pendingApps = applications.filter(a => a.status === 'pending');
  const acceptedApps = applications.filter(a => a.status === 'accepted');
  const otherApps = applications.filter(a => !['pending', 'accepted'].includes(a.status));

  return (
    <div className="max-w-3xl mx-auto animate-fadeIn">
      <div className="mb-8">
        <h1 
          className="text-2xl sm:text-3xl font-bold text-[#1C1917]"
          style={{ fontFamily: 'Syne, sans-serif' }}
        >
          My Applications
        </h1>
        <p className="text-[#57534E] mt-1">
          Track the dates you've applied to
        </p>
      </div>

      {applications.length > 0 ? (
        <div className="space-y-8">
          {/* Accepted */}
          {acceptedApps.length > 0 && (
            <div>
              <h2 className="font-semibold text-lg text-[#1C1917] mb-4 flex items-center gap-2" style={{ fontFamily: 'Syne, sans-serif' }}>
                <div className="w-2 h-2 rounded-full bg-[#2A9D8F]" />
                Accepted ({acceptedApps.length})
              </h2>
              <div className="space-y-4">
                {acceptedApps.map((app, idx) => (
                  <ApplicationCard 
                    key={app.id} 
                    application={app} 
                    index={idx}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Pending */}
          {pendingApps.length > 0 && (
            <div>
              <h2 className="font-semibold text-lg text-[#1C1917] mb-4 flex items-center gap-2" style={{ fontFamily: 'Syne, sans-serif' }}>
                <div className="w-2 h-2 rounded-full bg-[#E9C46A]" />
                Pending ({pendingApps.length})
              </h2>
              <div className="space-y-4">
                {pendingApps.map((app, idx) => (
                  <ApplicationCard 
                    key={app.id} 
                    application={app} 
                    index={idx}
                    onWithdraw={() => setWithdrawId(app.id)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Other */}
          {otherApps.length > 0 && (
            <div>
              <h2 className="font-semibold text-lg text-[#1C1917] mb-4 flex items-center gap-2" style={{ fontFamily: 'Syne, sans-serif' }}>
                <div className="w-2 h-2 rounded-full bg-[#A8A29E]" />
                Past ({otherApps.length})
              </h2>
              <div className="space-y-4">
                {otherApps.map((app, idx) => (
                  <ApplicationCard 
                    key={app.id} 
                    application={app} 
                    index={idx}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-state-icon">
            <FileText className="w-10 h-10" />
          </div>
          <h3 className="text-xl font-bold text-[#1C1917] mb-2" style={{ fontFamily: 'Syne, sans-serif' }}>
            No applications yet
          </h3>
          <p className="text-[#57534E] mb-6">
            Browse dates and apply to ones that excite you!
          </p>
          <Link to="/">
            <Button className="btn-primary rounded-full px-6" data-testid="browse-dates-btn">
              <Heart className="w-4 h-4 mr-2" />
              Browse Dates
            </Button>
          </Link>
        </div>
      )}

      {/* Withdraw Dialog */}
      <AlertDialog open={!!withdrawId} onOpenChange={() => setWithdrawId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Withdraw application?</AlertDialogTitle>
            <AlertDialogDescription>
              You can reapply later if the date is still open.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="rounded-full">Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleWithdraw}
              className="rounded-full"
              data-testid="confirm-withdraw-btn"
            >
              Withdraw
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

function ApplicationCard({ application, index, onWithdraw }) {
  const datePost = application.date_post;
  const dateTime = datePost?.date_time ? parseISO(datePost.date_time) : null;

  return (
    <div 
      className="bg-white rounded-2xl border border-stone-200 p-5 animate-slideUp"
      style={{ animationDelay: `${index * 0.05}s` }}
      data-testid={`application-${application.id}`}
    >
      <div className="flex items-start justify-between mb-3">
        <Link to={datePost ? `/dates/${datePost.id}` : '#'}>
          <h3 className="font-semibold text-[#1C1917] hover:text-[#E76F51] transition-colors">
            {datePost?.title || 'Date Post'}
          </h3>
        </Link>
        <Badge className={getStatusColor(application.status)}>
          {application.status}
        </Badge>
      </div>

      {datePost && (
        <div className="flex flex-wrap gap-4 text-sm text-[#57534E] mb-4">
          {dateTime && (
            <>
              <div className="flex items-center gap-1">
                <Calendar className="w-4 h-4 text-[#A8A29E]" />
                <span>{format(dateTime, 'MMM d')}</span>
              </div>
              <div className="flex items-center gap-1">
                <Clock className="w-4 h-4 text-[#A8A29E]" />
                <span>{format(dateTime, 'h:mm a')}</span>
              </div>
            </>
          )}
          <div className="flex items-center gap-1">
            <MapPin className="w-4 h-4 text-[#A8A29E]" />
            <span>{datePost.city}</span>
          </div>
        </div>
      )}

      <div className="bg-[#FDFCF8] rounded-xl p-3 mb-4">
        <p className="text-sm text-[#57534E]">"{application.message}"</p>
      </div>

      <div className="flex items-center justify-between">
        <span className="text-xs text-[#A8A29E]">
          Applied {format(parseISO(application.created_at), 'MMM d, yyyy')}
        </span>
        {application.status === 'pending' && onWithdraw && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onWithdraw}
            className="text-[#A8A29E] hover:text-red-500"
            data-testid={`withdraw-btn-${application.id}`}
          >
            <X className="w-4 h-4 mr-1" />
            Withdraw
          </Button>
        )}
        {application.status === 'accepted' && (
          <Link to="/chat">
            <Button size="sm" className="rounded-full bg-[#2A9D8F] hover:bg-[#238B7E]">
              Go to Chat
            </Button>
          </Link>
        )}
      </div>
    </div>
  );
}
