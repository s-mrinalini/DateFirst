import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { 
  User, MapPin, Calendar, Ruler, Heart, Settings, 
  ChevronRight, Edit2, Save, Sparkles
} from 'lucide-react';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Slider } from '../components/ui/slider';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { useAuth } from '../context/AuthContext';

const DATE_TAGS = [
  'coffee', 'dinner', 'brunch', 'drinks', 'outdoors', 'hiking',
  'museum', 'art', 'music', 'movies', 'comedy', 'games',
  'fitness', 'cooking', 'wine', 'adventure', 'chill', 'active'
];

export default function ProfilePage() {
  const { user, profile, updateProfile, logout } = useAuth();
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  
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
      toast.error('Failed to update profile');
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
        <Link to="/settings">
          <Button variant="ghost" size="icon" data-testid="settings-btn">
            <Settings className="w-5 h-5" />
          </Button>
        </Link>
      </div>

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
                <Label>Photo URL</Label>
                <Input
                  value={formData.main_photo}
                  onChange={(e) => updateField('main_photo', e.target.value)}
                  className="mt-1 rounded-xl"
                />
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
