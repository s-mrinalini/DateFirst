import React from 'react';
import { Link } from 'react-router-dom';
import { format, parseISO } from 'date-fns';
import { 
  MapPin, 
  Calendar, 
  Clock, 
  Heart, 
  Users, 
  DollarSign,
  Check
} from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { Badge } from './ui/badge';

const DATE_IMAGES = {
  coffee: 'https://images.unsplash.com/photo-1734989591520-eb44771b9077?w=800',
  dinner: 'https://images.unsplash.com/photo-1663437555931-d385ee04b8d1?w=800',
  outdoors: 'https://images.unsplash.com/photo-1628531832865-989e137150ce?w=800',
  hiking: 'https://images.unsplash.com/photo-1628531832865-989e137150ce?w=800',
  museum: 'https://images.unsplash.com/photo-1696238378039-821fc376ebd4?w=800',
  wine: 'https://images.unsplash.com/photo-1650313525165-40c8132c0ae0?w=800',
  music: 'https://images.unsplash.com/photo-1557619403-65c9c14441c1?w=800',
  default: 'https://images.unsplash.com/photo-1734989591520-eb44771b9077?w=800',
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
    case 'i_pay': return 'They pay';
    case 'you_pay': return 'You pay';
    case 'split': return 'Split';
    case 'decide_later': return 'Decide later';
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

export const DateCard = ({ post, onLike, showStatus = false }) => {
  const imageUrl = post.image_url || getDateImage(post.tags);
  const dateTime = parseISO(post.date_time);

  const handleLikeClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (onLike) {
      onLike(post.id, post.is_liked);
    }
  };

  return (
    <Link 
      to={`/dates/${post.id}`}
      className="date-card block"
      data-testid={`date-card-${post.id}`}
    >
      {/* Image Section */}
      <div className="relative aspect-[4/3] overflow-hidden">
        <img 
          src={imageUrl} 
          alt={post.title}
          className="w-full h-full object-cover"
          loading="lazy"
        />
        
        {/* Status Badge */}
        {showStatus && post.status !== 'OPEN' && (
          <div className="absolute top-3 left-3">
            <span className={`status-chip ${getStatusChipClass(post.status)}`}>
              {post.status}
            </span>
          </div>
        )}

        {/* Like Button */}
        <button
          onClick={handleLikeClick}
          className={`absolute top-3 right-3 w-10 h-10 rounded-full flex items-center justify-center transition-all ${
            post.is_liked 
              ? 'bg-[#E76F51] text-white' 
              : 'bg-white/90 text-[#57534E] hover:bg-white hover:text-[#E76F51]'
          }`}
          data-testid={`like-btn-${post.id}`}
        >
          <Heart className="w-5 h-5" fill={post.is_liked ? 'currentColor' : 'none'} />
        </button>

        {/* Poster Info */}
        <div className="absolute bottom-3 left-3 flex items-center gap-2">
          <Avatar className="w-8 h-8 border-2 border-white">
            <AvatarImage src={post.poster_photo} />
            <AvatarFallback className="bg-[#2A9D8F] text-white text-xs">
              {post.poster_name?.[0]?.toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <span className="text-white text-sm font-medium drop-shadow-lg">
            {post.poster_name}
          </span>
        </div>
      </div>

      {/* Content Section */}
      <div className="p-5">
        {/* Tags */}
        <div className="flex flex-wrap gap-2 mb-3">
          {post.tags?.slice(0, 3).map((tag, idx) => (
            <span 
              key={idx} 
              className={`tag ${idx === 0 ? '' : 'tag-accent'}`}
            >
              {tag}
            </span>
          ))}
        </div>

        {/* Title */}
        <h3 
          className="font-bold text-lg text-[#1C1917] mb-3 line-clamp-2"
          style={{ fontFamily: 'Syne, sans-serif' }}
        >
          {post.title}
        </h3>

        {/* Details */}
        <div className="space-y-2 text-sm text-[#57534E]">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-[#A8A29E]" />
            <span>{format(dateTime, 'EEE, MMM d')}</span>
            <Clock className="w-4 h-4 text-[#A8A29E] ml-2" />
            <span>{format(dateTime, 'h:mm a')}</span>
          </div>
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-[#A8A29E]" />
            <span className="truncate">{post.place_name || post.city}</span>
          </div>
        </div>

        {/* Perforated Line */}
        <div className="perforated mt-4 pt-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1 text-sm">
                <DollarSign className="w-4 h-4 text-[#2A9D8F]" />
                <span className="text-[#57534E]">{getWhoPaysLabel(post.who_pays)}</span>
              </div>
              <div className="flex items-center gap-1 text-sm">
                <Users className="w-4 h-4 text-[#E9C46A]" />
                <span className="text-[#57534E]">{post.application_count || 0}</span>
              </div>
            </div>
            <div className="flex items-center gap-1 text-sm">
              <Heart className="w-4 h-4 text-[#E76F51]" />
              <span className="text-[#57534E]">{post.like_count || 0}</span>
            </div>
          </div>
        </div>

        {/* Applied Badge */}
        {post.has_applied && (
          <div className="mt-3 flex items-center gap-2 text-[#2A9D8F] text-sm font-medium">
            <Check className="w-4 h-4" />
            <span>Applied</span>
          </div>
        )}
      </div>
    </Link>
  );
};

export default DateCard;
