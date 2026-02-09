import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import axios from 'axios';
import { Star, ThumbsUp, Shield, Target, X, Send } from 'lucide-react';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const FEEDBACK_TAGS = [
  { id: 'great_conversation', label: 'Great conversation' },
  { id: 'felt_safe', label: 'Felt safe' },
  { id: 'punctual', label: 'Punctual' },
  { id: 'respectful', label: 'Respectful' },
  { id: 'fun', label: 'Fun' },
  { id: 'good_listener', label: 'Good listener' },
  { id: 'matched_photos', label: 'Matched photos' },
  { id: 'would_meet_again', label: 'Would meet again' },
];

function StarRating({ value, onChange, label, icon: Icon }) {
  return (
    <div className="flex items-center justify-between py-2">
      <div className="flex items-center gap-2">
        {Icon && <Icon className="w-4 h-4 text-[#57534E]" />}
        <span className="text-sm font-medium">{label}</span>
      </div>
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            onClick={() => onChange(star)}
            className="p-1 hover:scale-110 transition-transform"
          >
            <Star
              className={`w-6 h-6 ${
                star <= value
                  ? 'fill-[#E9C46A] text-[#E9C46A]'
                  : 'text-stone-300'
              }`}
            />
          </button>
        ))}
      </div>
    </div>
  );
}

export default function DateFeedback({ threadId, matchName, isOpen, onClose, onSubmitted }) {
  const [loading, setLoading] = useState(false);
  const [canSubmit, setCanSubmit] = useState(false);
  const [hasSubmitted, setHasSubmitted] = useState(false);
  
  const [feedback, setFeedback] = useState({
    overall_rating: 0,
    safety_rating: 0,
    accuracy_rating: 0,
    would_recommend: true,
    feedback_text: '',
    tags: []
  });

  useEffect(() => {
    if (threadId && isOpen) {
      checkFeedbackStatus();
    }
  }, [threadId, isOpen]);

  const checkFeedbackStatus = async () => {
    try {
      const response = await axios.get(`${API}/feedback/thread/${threadId}`);
      setCanSubmit(response.data.can_submit);
      setHasSubmitted(response.data.has_submitted);
    } catch (error) {
      console.error('Failed to check feedback status:', error);
    }
  };

  const toggleTag = (tagId) => {
    setFeedback(prev => ({
      ...prev,
      tags: prev.tags.includes(tagId)
        ? prev.tags.filter(t => t !== tagId)
        : [...prev.tags, tagId]
    }));
  };

  const handleSubmit = async () => {
    if (feedback.overall_rating === 0) {
      toast.error('Please rate your overall experience');
      return;
    }
    if (feedback.safety_rating === 0) {
      toast.error('Please rate how safe you felt');
      return;
    }
    if (feedback.accuracy_rating === 0) {
      toast.error('Please rate date accuracy');
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/feedback`, {
        thread_id: threadId,
        ...feedback
      });
      toast.success('Thank you for your feedback!');
      setHasSubmitted(true);
      if (onSubmitted) onSubmitted();
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit feedback');
    } finally {
      setLoading(false);
    }
  };

  if (hasSubmitted) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Feedback Already Submitted</DialogTitle>
            <DialogDescription>
              You have already submitted feedback for this date. Thank you!
            </DialogDescription>
          </DialogHeader>
          <Button onClick={onClose} className="w-full mt-4">Close</Button>
        </DialogContent>
      </Dialog>
    );
  }

  if (!canSubmit) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Date Not Confirmed</DialogTitle>
            <DialogDescription>
              You can only leave feedback after confirming a date plan. Once your date is confirmed, come back here to share your experience.
            </DialogDescription>
          </DialogHeader>
          <Button onClick={onClose} className="w-full mt-4">Got it</Button>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Star className="w-5 h-5 text-[#E9C46A]" />
            How was your date with {matchName}?
          </DialogTitle>
          <DialogDescription>
            Your feedback helps improve DateFirst and keeps the community safe.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Star Ratings */}
          <div className="space-y-2 border-b border-stone-100 pb-4">
            <StarRating
              value={feedback.overall_rating}
              onChange={(v) => setFeedback(prev => ({ ...prev, overall_rating: v }))}
              label="Overall Experience"
              icon={Star}
            />
            <StarRating
              value={feedback.safety_rating}
              onChange={(v) => setFeedback(prev => ({ ...prev, safety_rating: v }))}
              label="How safe did you feel?"
              icon={Shield}
            />
            <StarRating
              value={feedback.accuracy_rating}
              onChange={(v) => setFeedback(prev => ({ ...prev, accuracy_rating: v }))}
              label="Did the date match the idea?"
              icon={Target}
            />
          </div>

          {/* Would Recommend */}
          <div className="flex items-center justify-between py-2">
            <span className="text-sm font-medium">Would you recommend this person?</span>
            <div className="flex gap-2">
              <Button
                variant={feedback.would_recommend ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFeedback(prev => ({ ...prev, would_recommend: true }))}
                className={feedback.would_recommend ? 'bg-[#2A9D8F]' : ''}
              >
                <ThumbsUp className="w-4 h-4 mr-1" />
                Yes
              </Button>
              <Button
                variant={!feedback.would_recommend ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFeedback(prev => ({ ...prev, would_recommend: false }))}
                className={!feedback.would_recommend ? 'bg-red-500' : ''}
              >
                <ThumbsUp className="w-4 h-4 mr-1 rotate-180" />
                No
              </Button>
            </div>
          </div>

          {/* Tags */}
          <div>
            <p className="text-sm font-medium mb-3">What stood out? (optional)</p>
            <div className="flex flex-wrap gap-2">
              {FEEDBACK_TAGS.map(tag => (
                <Badge
                  key={tag.id}
                  variant={feedback.tags.includes(tag.id) ? 'default' : 'outline'}
                  className={`cursor-pointer transition-all ${
                    feedback.tags.includes(tag.id)
                      ? 'bg-[#E76F51] hover:bg-[#D65D40]'
                      : 'hover:bg-stone-100'
                  }`}
                  onClick={() => toggleTag(tag.id)}
                >
                  {tag.label}
                </Badge>
              ))}
            </div>
          </div>

          {/* Written Feedback */}
          <div>
            <p className="text-sm font-medium mb-2">Any additional thoughts? (optional)</p>
            <Textarea
              value={feedback.feedback_text}
              onChange={(e) => setFeedback(prev => ({ ...prev, feedback_text: e.target.value }))}
              placeholder="Share your experience..."
              className="resize-none"
              rows={3}
              maxLength={500}
            />
            <p className="text-xs text-[#A8A29E] mt-1 text-right">
              {feedback.feedback_text.length}/500
            </p>
          </div>
        </div>

        <div className="flex gap-3 pt-4 border-t border-stone-100">
          <Button variant="outline" onClick={onClose} className="flex-1">
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={loading}
            className="flex-1 bg-[#E76F51] hover:bg-[#D65D40]"
          >
            {loading ? 'Submitting...' : (
              <>
                <Send className="w-4 h-4 mr-2" />
                Submit Feedback
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
