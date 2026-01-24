import React from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Crown, Check, Eye, Heart, Sparkles, ArrowRight } from 'lucide-react';
import { Button } from '../components/ui/button';
import { useAuth } from '../context/AuthContext';

const FEATURES = [
  {
    icon: Eye,
    title: 'See Full Profiles',
    description: 'View job titles, interests, and extra photos of applicants',
  },
  {
    icon: Heart,
    title: 'Compatibility Scores',
    description: 'See how well you match with each applicant',
  },
  {
    icon: Sparkles,
    title: 'Intent Matching',
    description: 'Know if they want relationship, casual dating, or friendship',
  },
];

export default function UpgradePage() {
  const navigate = useNavigate();
  const { upgradeToPremium, isPremium } = useAuth();
  const [loading, setLoading] = React.useState(false);

  const handleUpgrade = async () => {
    setLoading(true);
    try {
      await upgradeToPremium();
      toast.success('Welcome to Premium!');
      navigate('/');
    } catch (error) {
      toast.error('Failed to upgrade');
    } finally {
      setLoading(false);
    }
  };

  if (isPremium) {
    return (
      <div className="max-w-lg mx-auto text-center py-12 animate-fadeIn">
        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-[#E9C46A] to-[#E76F51] flex items-center justify-center mx-auto mb-6">
          <Crown className="w-10 h-10 text-white" />
        </div>
        <h1 
          className="text-3xl font-bold text-[#1C1917] mb-3"
          style={{ fontFamily: 'Syne, sans-serif' }}
        >
          You're Premium!
        </h1>
        <p className="text-[#57534E] mb-8">
          Enjoy full access to all applicant details and compatibility scores.
        </p>
        <Button 
          onClick={() => navigate('/')}
          className="btn-primary rounded-full px-8"
        >
          Browse Dates
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto animate-fadeIn">
      {/* Hero */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-[#E9C46A]/20 to-[#E76F51]/20 text-[#E76F51] font-medium text-sm mb-6">
          <Crown className="w-4 h-4" />
          Premium Membership
        </div>
        <h1 
          className="text-3xl sm:text-4xl font-bold text-[#1C1917] mb-4"
          style={{ fontFamily: 'Syne, sans-serif' }}
        >
          Make better matches
        </h1>
        <p className="text-lg text-[#57534E] max-w-md mx-auto">
          Get full access to applicant profiles and compatibility insights.
        </p>
      </div>

      {/* Features */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-12">
        {FEATURES.map(({ icon: Icon, title, description }, idx) => (
          <div 
            key={idx}
            className="bg-white rounded-2xl border border-stone-200 p-6 text-center animate-slideUp"
            style={{ animationDelay: `${idx * 0.1}s` }}
          >
            <div className="w-12 h-12 rounded-xl bg-[#E76F51]/10 flex items-center justify-center mx-auto mb-4">
              <Icon className="w-6 h-6 text-[#E76F51]" />
            </div>
            <h3 className="font-semibold text-[#1C1917] mb-2">{title}</h3>
            <p className="text-sm text-[#57534E]">{description}</p>
          </div>
        ))}
      </div>

      {/* Pricing Card */}
      <div className="bg-gradient-to-br from-[#1C1917] to-[#292524] rounded-3xl p-8 text-white text-center">
        <p className="text-white/60 text-sm mb-2">Monthly</p>
        <div className="flex items-baseline justify-center gap-1 mb-6">
          <span className="text-5xl font-bold" style={{ fontFamily: 'Syne, sans-serif' }}>$9.99</span>
          <span className="text-white/60">/month</span>
        </div>

        <ul className="space-y-3 mb-8">
          {[
            'Full applicant profiles',
            'Compatibility scores',
            'Intent & interests visibility',
            'Priority support',
          ].map((item, idx) => (
            <li key={idx} className="flex items-center gap-3 text-left">
              <Check className="w-5 h-5 text-[#2A9D8F] flex-shrink-0" />
              <span>{item}</span>
            </li>
          ))}
        </ul>

        <Button
          onClick={handleUpgrade}
          disabled={loading}
          className="w-full bg-white text-[#1C1917] hover:bg-stone-100 rounded-full py-6 text-lg font-semibold"
          data-testid="upgrade-btn"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <span className="w-5 h-5 border-2 border-stone-300 border-t-stone-600 rounded-full animate-spin" />
              Processing...
            </span>
          ) : (
            <span className="flex items-center gap-2">
              Upgrade Now
              <ArrowRight className="w-5 h-5" />
            </span>
          )}
        </Button>

        <p className="text-xs text-white/40 mt-4">
          This is a demo. No real payment will be processed.
        </p>
      </div>
    </div>
  );
}
