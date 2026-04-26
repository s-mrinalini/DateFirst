import React, { useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import axios from 'axios';
import {
  User, MapPin, Calendar, Ruler, Heart, Settings,
  ChevronRight, Edit2, Save, Sparkles, Shield, BadgeCheck,
  Camera, Phone, Mail, Crown, BookOpen, Upload
} from 'lucide-react';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Slider } from '../components/ui/slider';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Badge } from '../components/ui/badge';
import { useAuth } from '../context/AuthContext';

const DATE_TAGS = [
  'coffee', 'dinner', 'brunch', 'drinks', 'outdoors', 'hiking',
  'museum', 'art', 'music', 'movies', 'comedy', 'games',
  'fitness', 'cooking', 'wine', 'adventure', 'chill', 'active'
];

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const MAX_PHOTO_BYTES = 5 * 1024 * 1024;
const ALLOWED_PHOTO_MIMES = ['image/jpeg', 'image/png', 'image/webp'];

export default function ProfilePage() {
  const { user, profile, updateProfile, logout, badges, emailVerified, photoVerified, phoneVerified } = useAuth();
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);
  const [photoUploading, setPhotoUploading] = useState(false);

  const handlePhotoSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > MAX_PHOTO_BYTES) { toast.error('Photo must be under 5MB'); e.target.value = ''; return; }
    if (!ALLOWED_PHOTO_MIMES.includes(file.type)) { toast.error('Photo must be JPEG, PNG, or WebP'); e.target.value = ''; return; }

    const localPreview = URL.createObjectURL(file);
    updateField('main_photo', localPreview);

    setPhotoUploading(true);
    const fd = new FormData();
    fd.append('file', file);
    try {
      const response = await axios.post(`${API}/upload/photo`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      updateField('main_photo', response.data.url);
      URL.revokeObjectURL(localPreview);
      toast.success('Photo uploaded');
    } catch (err) {
      URL.revokeObjectURL(localPreview);
      updateField('main_photo', profile?.main_photo || '');
      toast.error(err.response?.data?.detail || 'Upload failed');
    } finally {
      setPhotoUploading(false);
      e.target.value = '';
    }
  };
  
  const [formData, setFormData] = useState({
    first_name: profile?.first_name || '',
    main_photo: profile?.main_photo || '',
    city: profile?.city || '',
    distance_preference: profile?.distance_preference || 50,
    bio: profile?.bio || '',
    height: profile?.height || '',
    interested_in: profile?.interested_in || [],
    date_preferences: profile?.date_preferences || [],
    first_date_idea: profile?.first_date_idea || { title: '', description: '', tags: [], city: '' }
  });

  const updateField = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const toggleArrayItem = (field, item) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].includes(item)
        ? prev[field].filter(i => i !== item)
        : [...prev[field], item]
    }));
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      await updateProfile(formData);
      toast.success('Profile updated!');
      setEditing(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const calculateAge = (dob) => {
    if (!dob) return null;
    const today = new Date();
    const birth = new Date(dob);
    let age = today.getFullYear() - birth.getFullYear();
    const m = today.getMonth() - birth.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
    return age;
  };

  const age = calculateAge(profile?.date_of_birth);

  return (
    <div className="min-h-screen bg-[#FDFCF8] p-4 pb-24">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
          Profile
        </h1>
        <div className="flex items-center gap-2">
          {user?.is_admin && (
            <Link to="/admin">
              <Button variant="ghost" size="icon" data-testid="admin-btn" className="text-[#E76F51]">
                <Crown className="w-5 h-5" />
              </Button>
            </Link>
          )}
          <Link to="/settings">
            <Button variant="ghost" size="icon" data-testid="settings-btn">
              <Settings className="w-5 h-5" />
            </Button>
          </Link>
        </div>
      </div>

      {/* Verification Badges */}
      {badges && badges.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {badges.map((badge, idx) => (
            <Badge key={idx} variant="secondary" className="bg-[#2A9D8F]/10 text-[#2A9D8F]">
              <BadgeCheck className="w-3 h-3 mr-1" />
              {badge.label}
            </Badge>
          ))}
        </div>
      )}

      {/* Profile Card */}
      <div className="bg-white rounded-3xl shadow-lg overflow-hidden mb-6">
        {/* Photo */}
        <div className="relative aspect-square max-h-80">
          <img 
            src={editing ? formData.main_photo : profile?.main_photo}
            alt={profile?.first_name}
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
          
          <div className="absolute bottom-4 left-4 text-white">
            <h2 className="text-2xl font-bold" style={{ fontFamily: 'Syne, sans-serif' }}>
              {profile?.first_name}{age && `, ${age}`}
            </h2>
            <div className="flex items-center gap-1 text-white/80 mt-1">
              <MapPin className="w-4 h-4" />
              <span>{profile?.city}</span>
            </div>
          </div>

          <button
            onClick={() => setEditing(!editing)}
            className="absolute top-4 right-4 w-10 h-10 rounded-full bg-white/90 flex items-center justify-center text-[#1C1917] hover:bg-white transition-all"
            data-testid="edit-btn"
          >
            <Edit2 className="w-5 h-5" />
          </button>
        </div>

        {/* Info */}
        <div className="p-5">
          {editing ? (
            <div className="space-y-4">
              <div>
                <Label>Name</Label>
                <Input
                  value={formData.first_name}
                  onChange={(e) => updateField('first_name', e.target.value)}
                  className="mt-1 rounded-xl"
                />
              </div>
              <div>
                <Label>Photo</Label>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={handlePhotoSelect}
                  data-testid="profile-photo-file"
                />
                <div className="mt-1 flex items-center gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={photoUploading}
                    className="rounded-full"
                    data-testid="profile-photo-button"
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    {photoUploading ? 'Uploading...' : 'Replace photo'}
                  </Button>
                  <span className="text-xs text-[#A8A29E]">JPEG, PNG, or WebP — up to 5MB</span>
                </div>
              </div>
              <div>
                <Label>City</Label>
                <Input
                  value={formData.city}
                  onChange={(e) => updateField('city', e.target.value)}
                  className="mt-1 rounded-xl"
                />
              </div>
              <div>
                <Label>Distance ({formData.distance_preference} mi)</Label>
                <Slider
                  value={[formData.distance_preference]}
                  onValueChange={(v) => updateField('distance_preference', v[0])}
                  min={1}
                  max={100}
                  className="mt-2"
                />
              </div>
              <div>
                <Label>Bio (shown after match)</Label>
                <Textarea
                  value={formData.bio}
                  onChange={(e) => updateField('bio', e.target.value)}
                  className="mt-1 rounded-xl"
                  maxLength={300}
                />
              </div>
              <div>
                <Label>Height</Label>
                <Input
                  value={formData.height}
                  onChange={(e) => updateField('height', e.target.value)}
                  className="mt-1 rounded-xl"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <Button
                  variant="outline"
                  onClick={() => setEditing(false)}
                  className="flex-1 rounded-full"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={loading}
                  className="flex-1 rounded-full bg-[#E76F51] hover:bg-[#D65D40]"
                  data-testid="save-btn"
                >
                  {loading ? 'Saving...' : 'Save'}
                </Button>
              </div>
            </div>
          ) : (
            <>
              {profile?.bio && (
                <p className="text-[#57534E] mb-4">{profile.bio}</p>
              )}
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                {profile?.height && (
                  <div className="flex items-center gap-2 text-[#57534E]">
                    <Ruler className="w-4 h-4 text-[#A8A29E]" />
                    <span>{profile.height}</span>
                  </div>
                )}
                <div className="flex items-center gap-2 text-[#57534E]">
                  <Heart className="w-4 h-4 text-[#E76F51]" />
                  <span>
                    {profile?.interested_in?.map(g => g === 'male' ? 'Men' : 'Women').join(' & ')}
                  </span>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        <Link 
          to="/safety"
          className="bg-white rounded-2xl shadow-sm p-4 flex items-center gap-3 hover:shadow-md transition-all"
          data-testid="safety-center-link"
        >
          <div className="w-10 h-10 rounded-full bg-[#2A9D8F]/10 flex items-center justify-center">
            <Shield className="w-5 h-5 text-[#2A9D8F]" />
          </div>
          <div>
            <p className="font-semibold text-sm">Safety Center</p>
            <p className="text-xs text-[#A8A29E]">Trusted contacts, verify</p>
          </div>
        </Link>
        <Link 
          to="/templates"
          className="bg-white rounded-2xl shadow-sm p-4 flex items-center gap-3 hover:shadow-md transition-all"
          data-testid="templates-link"
        >
          <div className="w-10 h-10 rounded-full bg-[#E76F51]/10 flex items-center justify-center">
            <BookOpen className="w-5 h-5 text-[#E76F51]" />
          </div>
          <div>
            <p className="font-semibold text-sm">Date Ideas</p>
            <p className="text-xs text-[#A8A29E]">Browse templates</p>
          </div>
        </Link>
      </div>

      {/* First Date Idea */}
      <div className="bg-white rounded-2xl shadow-sm p-5 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-5 h-5 text-[#E76F51]" />
          <h3 className="font-bold text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
            Your First Date Idea
          </h3>
        </div>

        <div className="bg-gradient-to-r from-[#E76F51]/5 to-[#E9C46A]/5 rounded-xl p-4">
          <h4 className="font-bold text-[#1C1917] mb-2">
            {profile?.first_date_idea?.title || 'No idea yet'}
          </h4>
          <p className="text-sm text-[#57534E] mb-3">
            {profile?.first_date_idea?.description}
          </p>
          <div className="flex flex-wrap gap-2">
            {profile?.first_date_idea?.tags?.map((tag, idx) => (
              <span 
                key={idx}
                className="px-3 py-1 rounded-full text-xs font-medium bg-white text-[#2A9D8F] border border-[#2A9D8F]/20"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Date Preferences */}
      <div className="bg-white rounded-2xl shadow-sm p-5">
        <h3 className="font-bold text-[#1C1917] mb-4" style={{ fontFamily: 'Syne, sans-serif' }}>
          Your Vibes
        </h3>
        <div className="flex flex-wrap gap-2">
          {profile?.date_preferences?.map((pref, idx) => (
            <span 
              key={idx}
              className="px-3 py-1.5 rounded-full text-sm font-medium bg-[#E76F51]/10 text-[#E76F51] capitalize"
            >
              {pref}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
