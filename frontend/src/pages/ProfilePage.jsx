import React, { useState } from 'react';
import { toast } from 'sonner';
import { 
  User, 
  MapPin, 
  Briefcase, 
  Heart, 
  Camera,
  Save,
  Crown
} from 'lucide-react';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Checkbox } from '../components/ui/checkbox';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';

const GENDER_OPTIONS = [
  { value: 'male', label: 'Male' },
  { value: 'female', label: 'Female' },
  { value: 'non_binary', label: 'Non-binary' },
  { value: 'other', label: 'Other' },
];

const INTENT_OPTIONS = [
  { value: 'relationship', label: 'Looking for a relationship' },
  { value: 'casual', label: 'Casual dating' },
  { value: 'new_friends', label: 'Making new friends' },
];

const INTEREST_OPTIONS = [
  'coffee', 'dinner', 'hiking', 'museum', 'music', 'wine', 
  'photography', 'fitness', 'travel', 'books', 'movies', 'cooking',
  'art', 'outdoors', 'concerts', 'theater', 'sports', 'gaming'
];

export default function ProfilePage() {
  const { user, profile, updateProfile, isPremium } = useAuth();
  const [loading, setLoading] = useState(false);
  
  const [formData, setFormData] = useState({
    first_name: profile?.first_name || user?.first_name || '',
    age: profile?.age || '',
    gender: profile?.gender || '',
    preferred_genders: profile?.preferred_genders || [],
    city: profile?.city || '',
    bio: profile?.bio || '',
    profile_photo: profile?.profile_photo || '',
    job_title: profile?.job_title || '',
    interests: profile?.interests || [],
    intent: profile?.intent || '',
  });

  const handleChange = (field) => (e) => {
    setFormData(prev => ({ ...prev, [field]: e.target.value }));
  };

  const handleSelectChange = (field) => (value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const toggleInterest = (interest) => {
    setFormData(prev => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter(i => i !== interest)
        : [...prev.interests, interest]
    }));
  };

  const togglePreferredGender = (gender) => {
    setFormData(prev => ({
      ...prev,
      preferred_genders: prev.preferred_genders.includes(gender)
        ? prev.preferred_genders.filter(g => g !== gender)
        : [...prev.preferred_genders, gender]
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const dataToUpdate = {
        ...formData,
        age: formData.age ? parseInt(formData.age) : null,
      };
      
      await updateProfile(dataToUpdate);
      toast.success('Profile updated successfully');
    } catch (error) {
      toast.error('Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 
            className="text-2xl sm:text-3xl font-bold text-[#1C1917]"
            style={{ fontFamily: 'Syne, sans-serif' }}
          >
            Your Profile
          </h1>
          <p className="text-[#57534E] mt-1">
            Complete your profile to get better matches
          </p>
        </div>
        {isPremium && (
          <div className="premium-badge">
            <Crown className="w-3 h-3" />
            Premium
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Profile Photo */}
        <div className="bg-white rounded-2xl border border-stone-200 p-6">
          <h2 className="font-semibold text-lg text-[#1C1917] mb-4" style={{ fontFamily: 'Syne, sans-serif' }}>
            Profile Photo
          </h2>
          <div className="flex items-center gap-6">
            <Avatar className="w-24 h-24">
              <AvatarImage src={formData.profile_photo} />
              <AvatarFallback className="bg-[#2A9D8F] text-white text-2xl">
                {formData.first_name?.[0]?.toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <Label className="text-[#57534E]">Photo URL</Label>
              <Input
                placeholder="https://example.com/photo.jpg"
                value={formData.profile_photo}
                onChange={handleChange('profile_photo')}
                className="mt-1.5 rounded-xl"
                data-testid="profile-photo-input"
              />
              <p className="text-xs text-[#A8A29E] mt-1">
                Paste a URL to your profile photo
              </p>
            </div>
          </div>
        </div>

        {/* Basic Info */}
        <div className="bg-white rounded-2xl border border-stone-200 p-6">
          <h2 className="font-semibold text-lg text-[#1C1917] mb-4" style={{ fontFamily: 'Syne, sans-serif' }}>
            Basic Information
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label className="text-[#57534E]">First Name</Label>
              <Input
                value={formData.first_name}
                onChange={handleChange('first_name')}
                className="mt-1.5 rounded-xl"
                data-testid="profile-firstname"
              />
            </div>
            <div>
              <Label className="text-[#57534E]">Age</Label>
              <Input
                type="number"
                min="18"
                max="100"
                value={formData.age}
                onChange={handleChange('age')}
                className="mt-1.5 rounded-xl"
                data-testid="profile-age"
              />
            </div>
            <div>
              <Label className="text-[#57534E]">Gender</Label>
              <Select value={formData.gender} onValueChange={handleSelectChange('gender')}>
                <SelectTrigger className="mt-1.5 rounded-xl" data-testid="profile-gender">
                  <SelectValue placeholder="Select gender" />
                </SelectTrigger>
                <SelectContent>
                  {GENDER_OPTIONS.map(opt => (
                    <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-[#57534E]">City</Label>
              <div className="relative mt-1.5">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#A8A29E]" />
                <Input
                  placeholder="Your city"
                  value={formData.city}
                  onChange={handleChange('city')}
                  className="pl-10 rounded-xl"
                  data-testid="profile-city"
                />
              </div>
            </div>
          </div>
        </div>

        {/* About */}
        <div className="bg-white rounded-2xl border border-stone-200 p-6">
          <h2 className="font-semibold text-lg text-[#1C1917] mb-4" style={{ fontFamily: 'Syne, sans-serif' }}>
            About You
          </h2>
          <div className="space-y-4">
            <div>
              <Label className="text-[#57534E]">Bio</Label>
              <Textarea
                placeholder="Tell others about yourself..."
                value={formData.bio}
                onChange={handleChange('bio')}
                className="mt-1.5 rounded-xl min-h-[100px]"
                data-testid="profile-bio"
              />
            </div>
            <div>
              <Label className="text-[#57534E]">Job Title (Optional)</Label>
              <div className="relative mt-1.5">
                <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#A8A29E]" />
                <Input
                  placeholder="What do you do?"
                  value={formData.job_title}
                  onChange={handleChange('job_title')}
                  className="pl-10 rounded-xl"
                  data-testid="profile-job"
                />
              </div>
            </div>
            <div>
              <Label className="text-[#57534E]">What are you looking for?</Label>
              <Select value={formData.intent} onValueChange={handleSelectChange('intent')}>
                <SelectTrigger className="mt-1.5 rounded-xl" data-testid="profile-intent">
                  <SelectValue placeholder="Select intent" />
                </SelectTrigger>
                <SelectContent>
                  {INTENT_OPTIONS.map(opt => (
                    <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        {/* Preferences */}
        <div className="bg-white rounded-2xl border border-stone-200 p-6">
          <h2 className="font-semibold text-lg text-[#1C1917] mb-4" style={{ fontFamily: 'Syne, sans-serif' }}>
            Preferences
          </h2>
          <div>
            <Label className="text-[#57534E] mb-3 block">Interested in dating</Label>
            <div className="flex flex-wrap gap-3">
              {['male', 'female', 'non_binary'].map(gender => (
                <label 
                  key={gender}
                  className="flex items-center gap-2 cursor-pointer"
                >
                  <Checkbox
                    checked={formData.preferred_genders.includes(gender)}
                    onCheckedChange={() => togglePreferredGender(gender)}
                    data-testid={`pref-gender-${gender}`}
                  />
                  <span className="text-[#1C1917] capitalize">
                    {gender.replace('_', '-')}
                  </span>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* Interests */}
        <div className="bg-white rounded-2xl border border-stone-200 p-6">
          <h2 className="font-semibold text-lg text-[#1C1917] mb-4" style={{ fontFamily: 'Syne, sans-serif' }}>
            Interests
          </h2>
          <div className="flex flex-wrap gap-2">
            {INTEREST_OPTIONS.map(interest => (
              <button
                key={interest}
                type="button"
                onClick={() => toggleInterest(interest)}
                className={`filter-chip capitalize ${
                  formData.interests.includes(interest) ? 'active' : ''
                }`}
                data-testid={`interest-${interest}`}
              >
                {interest}
              </button>
            ))}
          </div>
        </div>

        {/* Submit */}
        <div className="flex items-center justify-between">
          {!isPremium && (
            <Link to="/upgrade">
              <Button 
                type="button" 
                variant="outline" 
                className="rounded-full border-[#E76F51] text-[#E76F51]"
              >
                <Crown className="w-4 h-4 mr-2" />
                Upgrade to Premium
              </Button>
            </Link>
          )}
          <Button
            type="submit"
            className="btn-primary rounded-full px-8 ml-auto"
            disabled={loading}
            data-testid="save-profile-btn"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Saving...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Save className="w-4 h-4" />
                Save Changes
              </span>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
