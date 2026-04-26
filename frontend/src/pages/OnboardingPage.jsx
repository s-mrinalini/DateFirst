import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import axios from 'axios';
import {
  Heart, Camera, MapPin, Calendar, User, Ruler,
  FileText, Coffee, ArrowLeft, ArrowRight, Check, Sparkles, Mail, Upload
} from 'lucide-react';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Slider } from '../components/ui/slider';
import { useAuth } from '../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const MAX_PHOTO_BYTES = 5 * 1024 * 1024;
const ALLOWED_PHOTO_MIMES = ['image/jpeg', 'image/png', 'image/webp'];

const DATE_TAGS = [
  'coffee', 'dinner', 'brunch', 'drinks', 'outdoors', 'hiking',
  'museum', 'art', 'music', 'movies', 'theater', 'comedy',
  'sports', 'fitness', 'cooking', 'wine', 'games', 'adventure',
  'chill', 'active', 'romantic', 'fun', 'creative', 'culture'
];

const STEPS = [
  { id: 1, title: 'Name & Photo', icon: Camera },
  { id: 2, title: 'Location', icon: MapPin },
  { id: 3, title: 'Birthday', icon: Calendar },
  { id: 4, title: 'About You', icon: User },
  { id: 5, title: 'Height', icon: Ruler },
  { id: 6, title: 'Bio', icon: FileText },
  { id: 7, title: 'Preferences', icon: Coffee },
  { id: 8, title: 'Your Invite', icon: Heart },
];

export default function OnboardingPage() {
  const navigate = useNavigate();
  const { user, setupProfile, verifyEmail, resendVerification } = useAuth();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  // Email verification gate state
  const [otpCode, setOtpCode] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [resending, setResending] = useState(false);

  // Photo upload state
  const fileInputRef = useRef(null);
  const [photoUploading, setPhotoUploading] = useState(false);

  const [formData, setFormData] = useState({
    first_name: '',
    main_photo: '',
    city: '',
    distance_preference: 25,
    date_of_birth: '',
    gender: '',
    interested_in: [],
    height: '',
    bio: '',
    date_preferences: [],
    first_date_idea: {
      title: '',
      description: '',
      tags: [],
      city: ''
    }
  });

  const handleVerify = async () => {
    if (otpCode.length !== 6) {
      toast.error('Enter the 6-digit code');
      return;
    }
    setVerifying(true);
    try {
      await verifyEmail(otpCode);
      toast.success('Email verified!');
      // AuthContext updates user.email_verified; the gate falls through automatically.
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Invalid code');
    } finally {
      setVerifying(false);
    }
  };

  const handleResend = async () => {
    setResending(true);
    try {
      await resendVerification();
      toast.success('New code sent — check your email or backend logs.');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Could not resend');
    } finally {
      setResending(false);
    }
  };

  const handlePhotoSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > MAX_PHOTO_BYTES) {
      toast.error('Photo must be under 5MB');
      e.target.value = '';
      return;
    }
    if (!ALLOWED_PHOTO_MIMES.includes(file.type)) {
      toast.error('Photo must be JPEG, PNG, or WebP');
      e.target.value = '';
      return;
    }

    // Show local preview immediately while the upload runs.
    const localPreview = URL.createObjectURL(file);
    updateField('main_photo', localPreview);

    setPhotoUploading(true);
    const fd = new FormData();
    fd.append('file', file);
    try {
      const response = await axios.post(`${API}/upload/photo`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      // Replace local preview URL with the real uploaded URL.
      updateField('main_photo', response.data.url);
      URL.revokeObjectURL(localPreview);
      toast.success('Photo uploaded');
    } catch (err) {
      URL.revokeObjectURL(localPreview);
      updateField('main_photo', '');
      toast.error(err.response?.data?.detail || 'Upload failed');
    } finally {
      setPhotoUploading(false);
      e.target.value = '';
    }
  };

  const updateField = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const updateIdea = (field, value) => {
    setFormData(prev => ({
      ...prev,
      first_date_idea: { ...prev.first_date_idea, [field]: value }
    }));
  };

  const toggleArrayItem = (field, item) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].includes(item)
        ? prev[field].filter(i => i !== item)
        : [...prev[field], item]
    }));
  };

  const toggleIdeaTag = (tag) => {
    setFormData(prev => ({
      ...prev,
      first_date_idea: {
        ...prev.first_date_idea,
        tags: prev.first_date_idea.tags.includes(tag)
          ? prev.first_date_idea.tags.filter(t => t !== tag)
          : prev.first_date_idea.tags.length < 5 
            ? [...prev.first_date_idea.tags, tag]
            : prev.first_date_idea.tags
      }
    }));
  };

  const validateStep = () => {
    switch (step) {
      case 1:
        if (!formData.first_name.trim()) { toast.error('Enter your name'); return false; }
        if (!formData.main_photo.trim()) { toast.error('Add your photo'); return false; }
        if (photoUploading) { toast.error('Photo is still uploading'); return false; }
        return true;
      case 2:
        if (!formData.city.trim()) { toast.error('Enter your city'); return false; }
        return true;
      case 3:
        if (!formData.date_of_birth) { toast.error('Enter your birthday'); return false; }
        const age = new Date().getFullYear() - new Date(formData.date_of_birth).getFullYear();
        if (age < 18) { toast.error('Must be 18+'); return false; }
        return true;
      case 4:
        if (!formData.gender) { toast.error('Select your gender'); return false; }
        if (formData.interested_in.length === 0) { toast.error('Select who you\'re interested in'); return false; }
        return true;
      case 8:
        if (!formData.first_date_idea.title.trim()) { toast.error('Add a title for your date idea'); return false; }
        if (!formData.first_date_idea.description.trim()) { toast.error('Describe your date idea'); return false; }
        if (!formData.first_date_idea.city.trim()) { 
          updateIdea('city', formData.city);
        }
        return true;
      default:
        return true;
    }
  };

  const nextStep = () => {
    if (validateStep()) {
      if (step < 8) setStep(step + 1);
      else handleSubmit();
    }
  };

  const prevStep = () => {
    if (step > 1) setStep(step - 1);
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const data = {
        ...formData,
        first_date_idea: {
          ...formData.first_date_idea,
          city: formData.first_date_idea.city || formData.city
        }
      };
      await setupProfile(data);
      toast.success('Profile complete! Let\'s find your match!');
      navigate('/');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save profile');
    } finally {
      setLoading(false);
    }
  };

  const progress = (step / 8) * 100;

  // Email verification gate — must come before profile setup. Backend rejects
  // /profile/setup until the user verifies their email.
  if (!user?.email_verified) {
    return (
      <div className="min-h-screen bg-[#FDFCF8] flex flex-col">
        <div className="p-4 flex items-center gap-2">
          <Heart className="w-6 h-6 text-[#E76F51]" fill="#E76F51" />
          <span className="font-bold text-lg" style={{ fontFamily: 'Syne, sans-serif' }}>DateFirst</span>
        </div>
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="w-full max-w-md">
            <div className="text-center mb-8">
              <Mail className="w-12 h-12 text-[#E76F51] mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
                Verify your email
              </h2>
              <p className="text-[#57534E] mt-2">
                We sent a 6-digit code to <strong>{user?.email}</strong>
              </p>
              <p className="text-xs text-[#A8A29E] mt-3 px-4">
                Check your email for the verification code. If testing locally,
                check the backend logs for the OTP.
              </p>
            </div>

            <div className="space-y-4">
              <Input
                placeholder="123456"
                inputMode="numeric"
                maxLength={6}
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                className="text-center text-2xl tracking-[0.5em] h-14 rounded-xl"
                data-testid="verify-otp-input"
              />
              <Button
                onClick={handleVerify}
                disabled={verifying || otpCode.length !== 6}
                className="w-full h-12 bg-[#E76F51] hover:bg-[#D65D40] rounded-xl text-base font-semibold"
                data-testid="verify-submit"
              >
                {verifying ? 'Verifying...' : 'Verify email'}
              </Button>
              <button
                type="button"
                onClick={handleResend}
                disabled={resending}
                className="w-full text-sm text-[#57534E] hover:text-[#E76F51] disabled:opacity-50 py-2"
                data-testid="verify-resend"
              >
                {resending ? 'Sending...' : "Didn't get it? Resend code"}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FDFCF8] flex flex-col">
      {/* Progress Bar */}
      <div className="h-1 bg-stone-200">
        <div
          className="h-full bg-gradient-to-r from-[#E76F51] to-[#E9C46A] transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Header */}
      <div className="p-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Heart className="w-6 h-6 text-[#E76F51]" fill="#E76F51" />
          <span className="font-bold text-lg" style={{ fontFamily: 'Syne, sans-serif' }}>DateFirst</span>
        </div>
        <span className="text-sm text-[#57534E]">Step {step} of 8</span>
      </div>

      {/* Content */}
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-md animate-fadeIn">
          {/* Step 1: Name & Photo */}
          {step === 1 && (
            <div className="space-y-6">
              <div className="text-center mb-8">
                <Camera className="w-12 h-12 text-[#E76F51] mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
                  Let's start with you
                </h2>
                <p className="text-[#57534E] mt-2">Your first name and photo</p>
              </div>
              
              <div>
                <Label>First Name</Label>
                <Input
                  placeholder="Your first name"
                  value={formData.first_name}
                  onChange={(e) => updateField('first_name', e.target.value)}
                  className="mt-1.5 rounded-xl h-12"
                  data-testid="onboard-name"
                />
              </div>
              
              <div>
                <Label>Profile Photo</Label>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={handlePhotoSelect}
                  data-testid="onboard-photo-file"
                />
                <div className="mt-3 flex flex-col items-center gap-3">
                  {formData.main_photo ? (
                    <div className="relative">
                      <img
                        src={formData.main_photo}
                        alt="Preview"
                        className="w-32 h-32 rounded-full object-cover border-4 border-white shadow-lg"
                      />
                      {photoUploading && (
                        <div className="absolute inset-0 rounded-full bg-black/40 flex items-center justify-center">
                          <span className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="w-32 h-32 rounded-full bg-stone-100 flex items-center justify-center border-2 border-dashed border-stone-300">
                      <Camera className="w-10 h-10 text-stone-400" />
                    </div>
                  )}
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={photoUploading}
                    className="rounded-full"
                    data-testid="onboard-photo-button"
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    {photoUploading
                      ? 'Uploading...'
                      : formData.main_photo
                        ? 'Replace photo'
                        : 'Choose photo'}
                  </Button>
                  <p className="text-xs text-[#A8A29E]">JPEG, PNG, or WebP — up to 5MB</p>
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Location */}
          {step === 2 && (
            <div className="space-y-6">
              <div className="text-center mb-8">
                <MapPin className="w-12 h-12 text-[#2A9D8F] mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
                  Where are you?
                </h2>
                <p className="text-[#57534E] mt-2">City only - we keep it private</p>
              </div>
              
              <div>
                <Label>City</Label>
                <Input
                  placeholder="e.g., Austin, Houston, NYC"
                  value={formData.city}
                  onChange={(e) => updateField('city', e.target.value)}
                  className="mt-1.5 rounded-xl h-12"
                  data-testid="onboard-city"
                />
              </div>
              
              <div>
                <Label>How far would you travel? ({formData.distance_preference} miles)</Label>
                <Slider
                  value={[formData.distance_preference]}
                  onValueChange={(v) => updateField('distance_preference', v[0])}
                  min={1}
                  max={100}
                  step={1}
                  className="mt-4"
                  data-testid="onboard-distance"
                />
                <div className="flex justify-between text-xs text-[#A8A29E] mt-1">
                  <span>1 mi</span>
                  <span>100 mi</span>
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Birthday */}
          {step === 3 && (
            <div className="space-y-6">
              <div className="text-center mb-8">
                <Calendar className="w-12 h-12 text-[#E9C46A] mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
                  When's your birthday?
                </h2>
                <p className="text-[#57534E] mt-2">We won't show this publicly</p>
              </div>
              
              <div>
                <Label>Date of Birth</Label>
                <Input
                  type="date"
                  value={formData.date_of_birth}
                  onChange={(e) => updateField('date_of_birth', e.target.value)}
                  className="mt-1.5 rounded-xl h-12"
                  max={new Date(new Date().setFullYear(new Date().getFullYear() - 18)).toISOString().split('T')[0]}
                  data-testid="onboard-dob"
                />
              </div>
            </div>
          )}

          {/* Step 4: Gender & Interested In */}
          {step === 4 && (
            <div className="space-y-6">
              <div className="text-center mb-8">
                <User className="w-12 h-12 text-[#E76F51] mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
                  About you
                </h2>
              </div>
              
              <div>
                <Label className="mb-3 block">I am a...</Label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { value: 'male', label: 'Man' },
                    { value: 'female', label: 'Woman' },
                    { value: 'non_binary', label: 'Non-binary' }
                  ].map(opt => (
                    <button
                      key={opt.value}
                      onClick={() => updateField('gender', opt.value)}
                      className={`p-4 rounded-xl border-2 transition-all ${
                        formData.gender === opt.value
                          ? 'border-[#E76F51] bg-[#E76F51]/5'
                          : 'border-stone-200 hover:border-stone-300'
                      }`}
                      data-testid={`gender-${opt.value}`}
                    >
                      <span className="font-medium">{opt.label}</span>
                    </button>
                  ))}
                </div>
              </div>
              
              <div>
                <Label className="mb-3 block">Interested in...</Label>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { value: 'male', label: 'Men' },
                    { value: 'female', label: 'Women' }
                  ].map(opt => (
                    <button
                      key={opt.value}
                      onClick={() => toggleArrayItem('interested_in', opt.value)}
                      className={`p-4 rounded-xl border-2 transition-all ${
                        formData.interested_in.includes(opt.value)
                          ? 'border-[#2A9D8F] bg-[#2A9D8F]/5'
                          : 'border-stone-200 hover:border-stone-300'
                      }`}
                      data-testid={`interested-${opt.value}`}
                    >
                      <span className="font-medium">{opt.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 5: Height (Optional) */}
          {step === 5 && (
            <div className="space-y-6">
              <div className="text-center mb-8">
                <Ruler className="w-12 h-12 text-[#2A9D8F] mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
                  How tall are you?
                </h2>
                <p className="text-[#57534E] mt-2">Optional - skip if you prefer</p>
              </div>
              
              <div>
                <Label>Height</Label>
                <Input
                  placeholder="e.g., 5'8 or 173cm"
                  value={formData.height}
                  onChange={(e) => updateField('height', e.target.value)}
                  className="mt-1.5 rounded-xl h-12"
                  data-testid="onboard-height"
                />
              </div>
            </div>
          )}

          {/* Step 6: Bio (Optional) */}
          {step === 6 && (
            <div className="space-y-6">
              <div className="text-center mb-8">
                <FileText className="w-12 h-12 text-[#E9C46A] mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
                  A little about you
                </h2>
                <p className="text-[#57534E] mt-2">Optional - shown after you match</p>
              </div>
              
              <div>
                <Label>Bio</Label>
                <Textarea
                  placeholder="What makes you interesting?"
                  value={formData.bio}
                  onChange={(e) => updateField('bio', e.target.value)}
                  className="mt-1.5 rounded-xl min-h-[120px]"
                  maxLength={300}
                  data-testid="onboard-bio"
                />
                <p className="text-xs text-[#A8A29E] mt-1 text-right">{formData.bio.length}/300</p>
              </div>
            </div>
          )}

          {/* Step 7: Date Preferences */}
          {step === 7 && (
            <div className="space-y-6">
              <div className="text-center mb-8">
                <Coffee className="w-12 h-12 text-[#E76F51] mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
                  Your vibe
                </h2>
                <p className="text-[#57534E] mt-2">What kind of dates do you enjoy?</p>
              </div>
              
              <div className="flex flex-wrap gap-2">
                {DATE_TAGS.map(tag => (
                  <button
                    key={tag}
                    onClick={() => toggleArrayItem('date_preferences', tag)}
                    className={`px-4 py-2 rounded-full border transition-all capitalize ${
                      formData.date_preferences.includes(tag)
                        ? 'bg-[#E76F51] text-white border-[#E76F51]'
                        : 'bg-white border-stone-200 text-[#57534E] hover:border-stone-300'
                    }`}
                    data-testid={`pref-${tag}`}
                  >
                    {tag}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 8: First Date Idea */}
          {step === 8 && (
            <div className="space-y-6">
              <div className="text-center mb-8">
                <Sparkles className="w-12 h-12 text-[#E76F51] mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
                  Your perfect first date
                </h2>
                <p className="text-[#57534E] mt-2">This is what others will see!</p>
              </div>
              
              <div>
                <Label>Title</Label>
                <Input
                  placeholder="e.g., Coffee + Bookstore Wander"
                  value={formData.first_date_idea.title}
                  onChange={(e) => updateIdea('title', e.target.value)}
                  className="mt-1.5 rounded-xl h-12"
                  maxLength={60}
                  data-testid="idea-title"
                />
              </div>
              
              <div>
                <Label>Description</Label>
                <Textarea
                  placeholder="Describe your ideal first date... What's the vibe? What would you do?"
                  value={formData.first_date_idea.description}
                  onChange={(e) => updateIdea('description', e.target.value)}
                  className="mt-1.5 rounded-xl min-h-[100px]"
                  maxLength={200}
                  data-testid="idea-description"
                />
                <p className="text-xs text-[#A8A29E] mt-1 text-right">{formData.first_date_idea.description.length}/200</p>
              </div>
              
              <div>
                <Label className="mb-2 block">Tags (up to 5)</Label>
                <div className="flex flex-wrap gap-2">
                  {DATE_TAGS.slice(0, 12).map(tag => (
                    <button
                      key={tag}
                      onClick={() => toggleIdeaTag(tag)}
                      className={`px-3 py-1.5 rounded-full border text-sm transition-all capitalize ${
                        formData.first_date_idea.tags.includes(tag)
                          ? 'bg-[#2A9D8F] text-white border-[#2A9D8F]'
                          : 'bg-white border-stone-200 text-[#57534E]'
                      }`}
                      data-testid={`idea-tag-${tag}`}
                    >
                      {tag}
                    </button>
                  ))}
                </div>
              </div>
              
              <div>
                <Label>Area (city)</Label>
                <Input
                  placeholder={formData.city || "City name"}
                  value={formData.first_date_idea.city}
                  onChange={(e) => updateIdea('city', e.target.value)}
                  className="mt-1.5 rounded-xl h-12"
                  data-testid="idea-city"
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <div className="p-6 flex justify-between">
        <Button
          variant="outline"
          onClick={prevStep}
          disabled={step === 1}
          className="rounded-full px-6"
          data-testid="prev-btn"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>

        <Button
          onClick={nextStep}
          disabled={loading}
          className="rounded-full px-6 bg-[#E76F51] hover:bg-[#D65D40]"
          data-testid="next-btn"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Saving...
            </span>
          ) : step === 8 ? (
            <span className="flex items-center gap-2">
              <Check className="w-4 h-4" />
              Finish
            </span>
          ) : (
            <span className="flex items-center gap-2">
              Next
              <ArrowRight className="w-4 h-4" />
            </span>
          )}
        </Button>
      </div>
    </div>
  );
}
