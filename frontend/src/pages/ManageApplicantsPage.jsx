import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { ArrowLeft, Users, Crown, Check } from 'lucide-react';
import { Button } from '../components/ui/button';
import { ApplicantCard } from '../components/ApplicantCard';
import { useAuth } from '../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function ManageApplicantsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, isPremium } = useAuth();
  
  const [post, setPost] = useState(null);
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [accepting, setAccepting] = useState(null);

  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = async () => {
    try {
      const [postRes, appsRes] = await Promise.all([
        axios.get(`${API}/dates/${id}`),
        axios.get(`${API}/dates/${id}/applications`)
      ]);
      
      if (postRes.data.poster_id !== user?.id) {
        toast.error('Not authorized');
        navigate('/');
        return;
      }
      
      setPost(postRes.data);
      setApplications(appsRes.data);
    } catch (error) {
      toast.error('Failed to load data');
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = async (applicationId) => {
    setAccepting(applicationId);
    try {
      const response = await axios.post(`${API}/applications/${applicationId}/accept`);
      toast.success('Application accepted! Chat started.');
      navigate(`/chat/${response.data.thread_id}`);
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to accept application';
      toast.error(message);
    } finally {
      setAccepting(null);
    }
  };

  const handleDecline = async (applicationId) => {
    // For now, we just visually mark it - in a full app we'd have a decline endpoint
    setApplications(prev => prev.filter(app => app.id !== applicationId));
    toast.success('Application passed');
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="h-8 w-1/3 skeleton rounded mb-6" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white rounded-2xl border p-6">
              <div className="flex gap-4 mb-4">
                <div className="w-20 h-20 skeleton rounded-xl" />
                <div className="flex-1 space-y-2">
                  <div className="h-5 w-1/2 skeleton rounded" />
                  <div className="h-4 w-1/3 skeleton rounded" />
                </div>
              </div>
              <div className="h-16 skeleton rounded-xl" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!post) return null;

  const pendingApps = applications.filter(app => app.status === 'pending');
  const acceptedApp = applications.find(app => app.status === 'accepted');

  return (
    <div className="max-w-4xl mx-auto animate-fadeIn">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <Button
            variant="ghost"
            onClick={() => navigate(-1)}
            className="-ml-2 mb-2"
            data-testid="back-btn"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <h1 
            className="text-2xl sm:text-3xl font-bold text-[#1C1917]"
            style={{ fontFamily: 'Syne, sans-serif' }}
          >
            Manage Applicants
          </h1>
          <p className="text-[#57534E] mt-1">
            {post.title}
          </p>
        </div>
        
        <div className={`status-chip ${post.status === 'OPEN' ? 'status-open' : 'status-selected'}`}>
          {post.status}
        </div>
      </div>

      {/* Premium Upsell */}
      {!isPremium && pendingApps.length > 0 && (
        <div className="bg-gradient-to-r from-[#E76F51]/10 to-[#E9C46A]/10 rounded-2xl p-6 mb-8 border border-[#E76F51]/20">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-[#E76F51]/20 flex items-center justify-center">
              <Crown className="w-6 h-6 text-[#E76F51]" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-[#1C1917] mb-1" style={{ fontFamily: 'Syne, sans-serif' }}>
                Unlock full applicant profiles
              </h3>
              <p className="text-sm text-[#57534E] mb-3">
                See job titles, interests, compatibility scores, and more to make better decisions.
              </p>
              <Link to="/upgrade">
                <Button className="btn-primary rounded-full px-6" data-testid="upgrade-btn">
                  Upgrade to Premium
                </Button>
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Accepted Application */}
      {acceptedApp && (
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Check className="w-5 h-5 text-[#2A9D8F]" />
            <h2 className="font-semibold text-lg text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
              Accepted
            </h2>
          </div>
          <ApplicantCard
            application={acceptedApp}
            isPremium={isPremium}
            dateStatus={post.status}
          />
        </div>
      )}

      {/* Pending Applications */}
      {pendingApps.length > 0 ? (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Users className="w-5 h-5 text-[#57534E]" />
            <h2 className="font-semibold text-lg text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
              {post.status === 'OPEN' ? 'Pending Applications' : 'Other Applicants'} ({pendingApps.length})
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {pendingApps.map((app, idx) => (
              <div 
                key={app.id}
                className="animate-slideUp"
                style={{ animationDelay: `${idx * 0.05}s` }}
              >
                <ApplicantCard
                  application={app}
                  isPremium={isPremium}
                  onAccept={handleAccept}
                  onDecline={handleDecline}
                  isAccepting={accepting === app.id}
                  dateStatus={post.status}
                />
              </div>
            ))}
          </div>
        </div>
      ) : (
        !acceptedApp && (
          <div className="empty-state">
            <div className="empty-state-icon">
              <Users className="w-10 h-10" />
            </div>
            <h3 className="text-xl font-bold text-[#1C1917] mb-2" style={{ fontFamily: 'Syne, sans-serif' }}>
              No applications yet
            </h3>
            <p className="text-[#57534E]">
              Share your date to get more applicants
            </p>
          </div>
        )
      )}
    </div>
  );
}
