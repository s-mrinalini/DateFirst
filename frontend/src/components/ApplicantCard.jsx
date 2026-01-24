import React from 'react';
import { 
  MapPin, 
  Briefcase, 
  Heart, 
  Lock,
  Crown,
  Check,
  X
} from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Link } from 'react-router-dom';

export const ApplicantCard = ({ 
  application, 
  isPremium, 
  onAccept, 
  onDecline,
  isAccepting,
  dateStatus
}) => {
  const isLocked = application.is_premium_locked && !isPremium;
  const canAct = dateStatus === 'OPEN' && application.status === 'pending';

  return (
    <div 
      className={`bg-white rounded-2xl border border-stone-200 overflow-hidden transition-all hover:shadow-md ${
        application.status === 'accepted' ? 'ring-2 ring-[#2A9D8F]' : ''
      }`}
      data-testid={`applicant-card-${application.id}`}
    >
      {/* Header with photo and basic info */}
      <div className="p-5">
        <div className="flex gap-4">
          <Avatar className="w-20 h-20 rounded-xl">
            <AvatarImage src={application.applicant_photo} className="object-cover" />
            <AvatarFallback className="bg-[#2A9D8F] text-white text-xl rounded-xl">
              {application.applicant_name?.[0]?.toUpperCase()}
            </AvatarFallback>
          </Avatar>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-bold text-lg text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
                {application.applicant_name}
              </h3>
              {application.applicant_age && (
                <span className="text-[#57534E]">{application.applicant_age}</span>
              )}
            </div>

            {application.applicant_city && (
              <div className="flex items-center gap-1 text-sm text-[#57534E] mb-2">
                <MapPin className="w-4 h-4 text-[#A8A29E]" />
                <span>{application.applicant_city}</span>
              </div>
            )}

            {application.applicant_bio && (
              <p className="text-sm text-[#57534E] line-clamp-2">
                {application.applicant_bio}
              </p>
            )}
          </div>
        </div>

        {/* Application message */}
        <div className="mt-4 p-3 bg-[#FDFCF8] rounded-xl">
          <p className="text-sm text-[#1C1917]">"{application.message}"</p>
        </div>

        {/* Status badge */}
        {application.status !== 'pending' && (
          <div className="mt-3">
            <Badge 
              variant={application.status === 'accepted' ? 'default' : 'secondary'}
              className={
                application.status === 'accepted' 
                  ? 'bg-[#2A9D8F] text-white' 
                  : 'bg-stone-100 text-[#57534E]'
              }
            >
              {application.status === 'accepted' ? 'Accepted' : 'Declined'}
            </Badge>
          </div>
        )}
      </div>

      {/* Premium Section */}
      <div className={`border-t border-stone-200 p-5 ${isLocked ? 'relative' : ''}`}>
        {isLocked ? (
          <>
            {/* Locked overlay */}
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-white/80 to-white flex items-center justify-center">
              <Link to="/upgrade">
                <Button 
                  variant="outline" 
                  className="rounded-full border-2 border-[#E76F51] text-[#E76F51] hover:bg-[#E76F51] hover:text-white"
                  data-testid="unlock-premium-btn"
                >
                  <Crown className="w-4 h-4 mr-2" />
                  Unlock with Premium
                </Button>
              </Link>
            </div>
            
            {/* Blurred content */}
            <div className="blur-sm pointer-events-none">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-[#A8A29E] block mb-1">Job</span>
                  <span className="text-[#1C1917]">Software Engineer</span>
                </div>
                <div>
                  <span className="text-[#A8A29E] block mb-1">Looking for</span>
                  <span className="text-[#1C1917]">Relationship</span>
                </div>
                <div>
                  <span className="text-[#A8A29E] block mb-1">Compatibility</span>
                  <span className="text-[#2A9D8F] font-semibold">85%</span>
                </div>
                <div>
                  <span className="text-[#A8A29E] block mb-1">Interests</span>
                  <span className="text-[#1C1917]">Coffee, Hiking</span>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="grid grid-cols-2 gap-3 text-sm">
            {application.applicant_job_title && (
              <div>
                <span className="text-[#A8A29E] block mb-1">Job</span>
                <div className="flex items-center gap-1 text-[#1C1917]">
                  <Briefcase className="w-4 h-4 text-[#A8A29E]" />
                  <span>{application.applicant_job_title}</span>
                </div>
              </div>
            )}
            {application.applicant_intent && (
              <div>
                <span className="text-[#A8A29E] block mb-1">Looking for</span>
                <div className="flex items-center gap-1 text-[#1C1917]">
                  <Heart className="w-4 h-4 text-[#E76F51]" />
                  <span className="capitalize">{application.applicant_intent.replace('_', ' ')}</span>
                </div>
              </div>
            )}
            {application.compatibility_score !== null && (
              <div>
                <span className="text-[#A8A29E] block mb-1">Compatibility</span>
                <span className={`font-semibold ${
                  application.compatibility_score >= 70 ? 'text-[#2A9D8F]' : 
                  application.compatibility_score >= 50 ? 'text-[#E9C46A]' : 'text-[#57534E]'
                }`}>
                  {application.compatibility_score}%
                </span>
              </div>
            )}
            {application.applicant_interests && application.applicant_interests.length > 0 && (
              <div>
                <span className="text-[#A8A29E] block mb-1">Interests</span>
                <div className="flex flex-wrap gap-1">
                  {application.applicant_interests.slice(0, 3).map((interest, idx) => (
                    <span key={idx} className="text-[#1C1917] capitalize">
                      {interest}{idx < Math.min(application.applicant_interests.length, 3) - 1 ? ',' : ''}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Action Buttons */}
      {canAct && (
        <div className="border-t border-stone-200 p-4 flex gap-3">
          <Button
            variant="outline"
            className="flex-1 rounded-full border-stone-300 hover:border-red-400 hover:text-red-500"
            onClick={() => onDecline && onDecline(application.id)}
            data-testid={`decline-btn-${application.id}`}
          >
            <X className="w-4 h-4 mr-2" />
            Pass
          </Button>
          <Button
            className="flex-1 rounded-full bg-[#2A9D8F] hover:bg-[#238B7E] text-white"
            onClick={() => onAccept && onAccept(application.id)}
            disabled={isAccepting}
            data-testid={`accept-btn-${application.id}`}
          >
            <Check className="w-4 h-4 mr-2" />
            {isAccepting ? 'Accepting...' : 'Accept'}
          </Button>
        </div>
      )}
    </div>
  );
};

export default ApplicantCard;
