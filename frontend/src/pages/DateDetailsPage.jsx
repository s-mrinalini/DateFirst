import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { format, parseISO } from 'date-fns';
import { 
  MapPin, 
  Calendar, 
  Clock, 
  Heart, 
  Users, 
  DollarSign,
  ArrowLeft,
  Share2,
  Flag,
  Edit,
  Trash2,
  Send,
  Check
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
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

const DATE_IMAGES = {
  coffee: 'https://images.unsplash.com/photo-1734989591520-eb44771b9077?w=1200',
  dinner: 'https://images.unsplash.com/photo-1663437555931-d385ee04b8d1?w=1200',
  outdoors: 'https://images.unsplash.com/photo-1628531832865-989e137150ce?w=1200',
  hiking: 'https://images.unsplash.com/photo-1628531832865-989e137150ce?w=1200',
  museum: 'https://images.unsplash.com/photo-1696238378039-821fc376ebd4?w=1200',
  default: 'https://images.unsplash.com/photo-1734989591520-eb44771b9077?w=1200',
};

const getDateImage = (tags) => {
  if (!tags || tags.length === 0) return DATE_IMAGES.default;
  for (const tag of tags) {
    if (DATE_IMAGES[tag.toLowerCase()]) {
      return DATE_IMAGES[tag.toLowerCase()];
    }
  }
  return DATE_IMAGES.default;
};

const getWhoPaysLabel = (whoPays) => {
  switch (whoPays) {
    case 'i_pay': return 'Host pays';
    case 'you_pay': return 'You pay';
    case 'split': return 'Split the cost';
    case 'decide_later': return 'Decide together';
    default: return whoPays;
  }
};

const getStatusChipClass = (status) => {
  switch (status) {
    case 'OPEN': return 'status-open';
    case 'SELECTED': return 'status-selected';
    case 'COMPLETED': return 'status-completed';
    case 'CANCELLED': return 'status-cancelled';
    default: return 'status-open';
  }
};

export default function DateDetailsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  
  const [post, setPost] = useState(null);
  const [loading, setLoading] = useState(true);
  const [applyDialogOpen, setApplyDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [reportDialogOpen, setReportDialogOpen] = useState(false);
  const [applicationMessage, setApplicationMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchPost();
  }, [id]);

  const fetchPost = async () => {
    try {
      const response = await axios.get(`${API}/dates/${id}`);
      setPost(response.data);
    } catch (error) {
      toast.error('Failed to load date');
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const handleLike = async () => {
    if (!isAuthenticated) {
      toast.error('Please sign in to like dates');
      return;
    }

    try {
      if (post.is_liked) {
        await axios.delete(`${API}/dates/${id}/like`);
      } else {
        await axios.post(`${API}/dates/${id}/like`);
      }
      setPost(prev => ({
        ...prev,
        is_liked: !prev.is_liked,
        like_count: prev.is_liked ? prev.like_count - 1 : prev.like_count + 1
      }));
    } catch (error) {
      toast.error('Failed to update like');
    }
  };

  const handleApply = async () => {
    if (!applicationMessage.trim()) {
      toast.error('Please add a message');
      return;
    }

    setSubmitting(true);
    try {
      await axios.post(`${API}/dates/${id}/apply`, {
        message: applicationMessage,
      });
      toast.success('Application submitted!');
      setApplyDialogOpen(false);
      setApplicationMessage('');
      fetchPost();
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to apply';
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    try {
      await axios.delete(`${API}/dates/${id}`);
      toast.success('Date deleted');
      navigate('/my-dates');
    } catch (error) {
      toast.error('Failed to delete date');
    }
  };

  const handleReport = async () => {
    try {
      await axios.post(`${API}/report`, {
        reported_post_id: id,
        reason: 'inappropriate',
      });
      toast.success('Report submitted');
      setReportDialogOpen(false);
    } catch (error) {
      toast.error('Failed to submit report');
    }
  };

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      toast.success('Link copied to clipboard');
    } catch (error) {
      toast.error('Failed to copy link');
    }
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="aspect-video skeleton rounded-2xl mb-6" />
        <div className="space-y-4">
          <div className="h-8 w-3/4 skeleton rounded" />
          <div className="h-4 w-full skeleton rounded" />
          <div className="h-4 w-2/3 skeleton rounded" />
        </div>
      </div>
    );
  }

  if (!post) return null;

  const isOwner = user?.id === post.poster_id;
  const canApply = isAuthenticated && !isOwner && post.status === 'OPEN' && !post.has_applied;
  const imageUrl = post.image_url || getDateImage(post.tags);
  const dateTime = parseISO(post.date_time);

  return (
    <div className="max-w-3xl mx-auto animate-fadeIn">
      {/* Back Button */}
      <Button
        variant="ghost"
        onClick={() => navigate(-1)}
        className="mb-4 -ml-2"
        data-testid="back-btn"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back
      </Button>

      {/* Hero Image */}
      <div className="relative aspect-video rounded-2xl overflow-hidden mb-6">
        <img 
          src={imageUrl} 
          alt={post.title}
          className="w-full h-full object-cover"
        />
        
        {/* Status Badge */}
        <div className="absolute top-4 left-4">
          <span className={`status-chip ${getStatusChipClass(post.status)}`}>
            {post.status}
          </span>
        </div>

        {/* Action Buttons */}
        <div className="absolute top-4 right-4 flex gap-2">
          <button
            onClick={handleLike}
            className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
              post.is_liked 
                ? 'bg-[#E76F51] text-white' 
                : 'bg-white/90 text-[#57534E] hover:bg-white hover:text-[#E76F51]'
            }`}
            data-testid="like-btn"
          >
            <Heart className="w-5 h-5" fill={post.is_liked ? 'currentColor' : 'none'} />
          </button>
          <button
            onClick={handleShare}
            className="w-10 h-10 rounded-full bg-white/90 text-[#57534E] flex items-center justify-center hover:bg-white"
            data-testid="share-btn"
          >
            <Share2 className="w-5 h-5" />
          </button>
        </div>

        {/* Poster Info */}
        <div className="absolute bottom-4 left-4 flex items-center gap-3 bg-white/90 backdrop-blur-sm rounded-full py-2 px-4">
          <Avatar className="w-10 h-10 border-2 border-white">
            <AvatarImage src={post.poster_photo} />
            <AvatarFallback className="bg-[#2A9D8F] text-white">
              {post.poster_name?.[0]?.toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div>
            <p className="font-semibold text-[#1C1917]">{post.poster_name}</p>
            <p className="text-xs text-[#57534E]">Host</p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Title & Tags */}
          <div>
            <div className="flex flex-wrap gap-2 mb-3">
              {post.tags?.map((tag, idx) => (
                <span key={idx} className={`tag ${idx === 0 ? '' : 'tag-accent'}`}>
                  {tag}
                </span>
              ))}
            </div>
            <h1 
              className="text-2xl sm:text-3xl font-bold text-[#1C1917]"
              style={{ fontFamily: 'Syne, sans-serif' }}
            >
              {post.title}
            </h1>
          </div>

          {/* Description */}
          <div className="bg-white rounded-2xl border border-stone-200 p-6">
            <h2 className="font-semibold text-[#1C1917] mb-3" style={{ fontFamily: 'Syne, sans-serif' }}>
              About this date
            </h2>
            <p className="text-[#57534E] whitespace-pre-wrap">{post.description}</p>
          </div>

          {/* Details */}
          <div className="bg-white rounded-2xl border border-stone-200 p-6">
            <h2 className="font-semibold text-[#1C1917] mb-4" style={{ fontFamily: 'Syne, sans-serif' }}>
              Details
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-[#2A9D8F]/10 flex items-center justify-center">
                  <Calendar className="w-5 h-5 text-[#2A9D8F]" />
                </div>
                <div>
                  <p className="text-sm text-[#A8A29E]">Date</p>
                  <p className="font-medium text-[#1C1917]">{format(dateTime, 'EEEE, MMMM d')}</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-[#E9C46A]/10 flex items-center justify-center">
                  <Clock className="w-5 h-5 text-[#E9C46A]" />
                </div>
                <div>
                  <p className="text-sm text-[#A8A29E]">Time</p>
                  <p className="font-medium text-[#1C1917]">{format(dateTime, 'h:mm a')}</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-[#E76F51]/10 flex items-center justify-center">
                  <MapPin className="w-5 h-5 text-[#E76F51]" />
                </div>
                <div>
                  <p className="text-sm text-[#A8A29E]">Location</p>
                  <p className="font-medium text-[#1C1917]">{post.place_name || post.city}</p>
                  {post.place_name && <p className="text-sm text-[#57534E]">{post.city}</p>}
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-stone-100 flex items-center justify-center">
                  <DollarSign className="w-5 h-5 text-[#57534E]" />
                </div>
                <div>
                  <p className="text-sm text-[#A8A29E]">Who pays</p>
                  <p className="font-medium text-[#1C1917]">{getWhoPaysLabel(post.who_pays)}</p>
                </div>
              </div>
            </div>
            {post.duration && (
              <p className="text-sm text-[#57534E] mt-4">
                Duration: {post.duration}
              </p>
            )}
          </div>

          {/* Owner Actions */}
          {isOwner && (
            <div className="flex gap-3">
              <Link to={`/dates/${id}/manage`} className="flex-1">
                <Button className="w-full rounded-full bg-[#2A9D8F] hover:bg-[#238B7E]" data-testid="manage-btn">
                  <Users className="w-4 h-4 mr-2" />
                  Manage Applicants ({post.application_count})
                </Button>
              </Link>
              <Button
                variant="outline"
                className="rounded-full"
                onClick={() => setDeleteDialogOpen(true)}
                data-testid="delete-btn"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Stats Card */}
          <div className="bg-white rounded-2xl border border-stone-200 p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Heart className="w-5 h-5 text-[#E76F51]" />
                <span className="font-semibold text-[#1C1917]">{post.like_count} likes</span>
              </div>
              <div className="flex items-center gap-2">
                <Users className="w-5 h-5 text-[#2A9D8F]" />
                <span className="font-semibold text-[#1C1917]">{post.application_count} applied</span>
              </div>
            </div>

            {canApply && (
              <Button
                className="w-full btn-primary rounded-full"
                onClick={() => setApplyDialogOpen(true)}
                data-testid="apply-btn"
              >
                <Send className="w-4 h-4 mr-2" />
                Apply to Join
              </Button>
            )}

            {post.has_applied && (
              <div className="flex items-center justify-center gap-2 py-3 px-4 bg-[#2A9D8F]/10 rounded-xl text-[#2A9D8F]">
                <Check className="w-5 h-5" />
                <span className="font-medium">You've applied</span>
              </div>
            )}

            {!isAuthenticated && (
              <Link to="/auth">
                <Button className="w-full btn-primary rounded-full" data-testid="signin-to-apply-btn">
                  Sign in to apply
                </Button>
              </Link>
            )}

            {isOwner && post.status === 'OPEN' && (
              <p className="text-center text-sm text-[#57534E]">
                You're the host of this date
              </p>
            )}
          </div>

          {/* Report */}
          {!isOwner && isAuthenticated && (
            <button
              onClick={() => setReportDialogOpen(true)}
              className="flex items-center gap-2 text-sm text-[#A8A29E] hover:text-[#E76F51] transition-colors"
              data-testid="report-btn"
            >
              <Flag className="w-4 h-4" />
              Report this date
            </button>
          )}
        </div>
      </div>

      {/* Apply Dialog */}
      <Dialog open={applyDialogOpen} onOpenChange={setApplyDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Syne, sans-serif' }}>Apply to join</DialogTitle>
            <DialogDescription>
              Tell {post.poster_name} why you'd enjoy this date
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Textarea
              placeholder="I'd love to join because..."
              value={applicationMessage}
              onChange={(e) => setApplicationMessage(e.target.value)}
              className="rounded-xl min-h-[120px]"
              maxLength={500}
              data-testid="application-message"
            />
            <p className="text-xs text-[#A8A29E] mt-1 text-right">
              {applicationMessage.length}/500
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setApplyDialogOpen(false)} className="rounded-full">
              Cancel
            </Button>
            <Button 
              onClick={handleApply} 
              disabled={submitting}
              className="btn-primary rounded-full"
              data-testid="submit-application-btn"
            >
              {submitting ? 'Submitting...' : 'Submit Application'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this date?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. All applications will be removed.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="rounded-full">Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleDelete}
              className="rounded-full bg-red-500 hover:bg-red-600"
              data-testid="confirm-delete-btn"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Report Dialog */}
      <AlertDialog open={reportDialogOpen} onOpenChange={setReportDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Report this date?</AlertDialogTitle>
            <AlertDialogDescription>
              If you believe this date violates our guidelines, please report it.
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
