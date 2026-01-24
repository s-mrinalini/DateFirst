import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import axios from 'axios';
import { format } from 'date-fns';
import { 
  MapPin, 
  Calendar as CalendarIcon, 
  Clock, 
  Users,
  DollarSign,
  Tag,
  ArrowLeft,
  ArrowRight,
  Sparkles
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
import { Calendar } from '../components/ui/calendar';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '../components/ui/popover';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const WHO_PAYS_OPTIONS = [
  { value: 'i_pay', label: "I'll pay", description: 'You cover the date' },
  { value: 'split', label: 'Split', description: 'Share the costs' },
  { value: 'you_pay', label: 'They pay', description: 'Your date covers it' },
  { value: 'decide_later', label: 'Decide later', description: 'Work it out together' },
];

const TAG_OPTIONS = [
  'coffee', 'dinner', 'brunch', 'drinks', 'hiking', 'outdoors', 
  'museum', 'art', 'music', 'concert', 'movie', 'theater',
  'sports', 'fitness', 'cooking', 'wine', 'travel', 'adventure',
  'casual', 'romantic', 'fun', 'creative'
];

const TIME_OPTIONS = [
  '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00',
  '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00'
];

export default function CreateDatePage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1);
  
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    city: '',
    place_name: '',
    map_link: '',
    date: null,
    time: '18:00',
    duration: '2-3 hours',
    who_pays: 'split',
    tags: [],
    preferred_genders: [],
    age_range_min: 21,
    age_range_max: 45,
    max_applicants: 10,
  });

  const handleChange = (field) => (e) => {
    setFormData(prev => ({ ...prev, [field]: e.target.value }));
  };

  const handleSelectChange = (field) => (value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const toggleTag = (tag) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.includes(tag)
        ? prev.tags.filter(t => t !== tag)
        : prev.tags.length < 5 ? [...prev.tags, tag] : prev.tags
    }));
  };

  const validateStep = (stepNum) => {
    if (stepNum === 1) {
      if (!formData.title.trim()) {
        toast.error('Please add a title');
        return false;
      }
      if (!formData.description.trim()) {
        toast.error('Please add a description');
        return false;
      }
    }
    if (stepNum === 2) {
      if (!formData.city.trim()) {
        toast.error('Please add a city');
        return false;
      }
      if (!formData.date) {
        toast.error('Please select a date');
        return false;
      }
    }
    return true;
  };

  const nextStep = () => {
    if (validateStep(step)) {
      setStep(prev => Math.min(prev + 1, 3));
    }
  };

  const prevStep = () => {
    setStep(prev => Math.max(prev - 1, 1));
  };

  const handleSubmit = async () => {
    if (!validateStep(1) || !validateStep(2)) return;
    
    setLoading(true);
    try {
      // Combine date and time
      const dateTime = new Date(formData.date);
      const [hours, minutes] = formData.time.split(':');
      dateTime.setHours(parseInt(hours), parseInt(minutes), 0, 0);

      const payload = {
        title: formData.title,
        description: formData.description,
        city: formData.city,
        place_name: formData.place_name || null,
        map_link: formData.map_link || null,
        date_time: dateTime.toISOString(),
        duration: formData.duration || null,
        who_pays: formData.who_pays,
        tags: formData.tags,
        preferred_genders: formData.preferred_genders.length > 0 ? formData.preferred_genders : null,
        age_range_min: formData.age_range_min,
        age_range_max: formData.age_range_max,
        max_applicants: formData.max_applicants,
      };

      const response = await axios.post(`${API}/dates`, payload);
      toast.success('Date posted successfully!');
      navigate(`/dates/${response.data.id}`);
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to create date';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto animate-fadeIn">
      {/* Header */}
      <div className="mb-8">
        <h1 
          className="text-2xl sm:text-3xl font-bold text-[#1C1917]"
          style={{ fontFamily: 'Syne, sans-serif' }}
        >
          Post a Date Idea
        </h1>
        <p className="text-[#57534E] mt-1">
          Share your perfect date and find someone to join you
        </p>
      </div>

      {/* Progress */}
      <div className="flex items-center gap-2 mb-8">
        {[1, 2, 3].map((s) => (
          <React.Fragment key={s}>
            <div 
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors ${
                step >= s 
                  ? 'bg-[#E76F51] text-white' 
                  : 'bg-stone-200 text-[#57534E]'
              }`}
            >
              {s}
            </div>
            {s < 3 && (
              <div className={`flex-1 h-1 rounded ${step > s ? 'bg-[#E76F51]' : 'bg-stone-200'}`} />
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Step 1: Basic Info */}
      {step === 1 && (
        <div className="bg-white rounded-2xl border border-stone-200 p-6 animate-slideUp">
          <h2 className="font-semibold text-lg text-[#1C1917] mb-6" style={{ fontFamily: 'Syne, sans-serif' }}>
            What's the plan?
          </h2>
          
          <div className="space-y-5">
            <div>
              <Label className="text-[#57534E]">Title *</Label>
              <Input
                placeholder="e.g., Sunset Picnic at the Park"
                value={formData.title}
                onChange={handleChange('title')}
                className="mt-1.5 rounded-xl"
                maxLength={100}
                data-testid="date-title"
              />
              <p className="text-xs text-[#A8A29E] mt-1">{formData.title.length}/100</p>
            </div>

            <div>
              <Label className="text-[#57534E]">Description *</Label>
              <Textarea
                placeholder="Describe your date idea. What makes it special? What can your date expect?"
                value={formData.description}
                onChange={handleChange('description')}
                className="mt-1.5 rounded-xl min-h-[120px]"
                maxLength={500}
                data-testid="date-description"
              />
              <p className="text-xs text-[#A8A29E] mt-1">{formData.description.length}/500</p>
            </div>

            <div>
              <Label className="text-[#57534E] mb-3 block">Tags (up to 5)</Label>
              <div className="flex flex-wrap gap-2">
                {TAG_OPTIONS.map(tag => (
                  <button
                    key={tag}
                    type="button"
                    onClick={() => toggleTag(tag)}
                    className={`filter-chip capitalize ${formData.tags.includes(tag) ? 'active' : ''}`}
                    data-testid={`date-tag-${tag}`}
                  >
                    {tag}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Step 2: Location & Time */}
      {step === 2 && (
        <div className="bg-white rounded-2xl border border-stone-200 p-6 animate-slideUp">
          <h2 className="font-semibold text-lg text-[#1C1917] mb-6" style={{ fontFamily: 'Syne, sans-serif' }}>
            When & Where?
          </h2>
          
          <div className="space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label className="text-[#57534E]">City *</Label>
                <div className="relative mt-1.5">
                  <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#A8A29E]" />
                  <Input
                    placeholder="e.g., Austin"
                    value={formData.city}
                    onChange={handleChange('city')}
                    className="pl-10 rounded-xl"
                    data-testid="date-city"
                  />
                </div>
              </div>
              <div>
                <Label className="text-[#57534E]">Place Name</Label>
                <Input
                  placeholder="e.g., Zilker Park"
                  value={formData.place_name}
                  onChange={handleChange('place_name')}
                  className="mt-1.5 rounded-xl"
                  data-testid="date-place"
                />
              </div>
            </div>

            <div>
              <Label className="text-[#57534E]">Map Link (Optional)</Label>
              <Input
                placeholder="https://maps.google.com/..."
                value={formData.map_link}
                onChange={handleChange('map_link')}
                className="mt-1.5 rounded-xl"
                data-testid="date-map-link"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label className="text-[#57534E]">Date *</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className="w-full mt-1.5 rounded-xl justify-start text-left font-normal"
                      data-testid="date-picker-trigger"
                    >
                      <CalendarIcon className="mr-2 h-4 w-4 text-[#A8A29E]" />
                      {formData.date ? format(formData.date, 'PPP') : 'Select date'}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={formData.date}
                      onSelect={(date) => setFormData(prev => ({ ...prev, date }))}
                      disabled={(date) => date < new Date()}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
              </div>
              <div>
                <Label className="text-[#57534E]">Time</Label>
                <Select value={formData.time} onValueChange={handleSelectChange('time')}>
                  <SelectTrigger className="mt-1.5 rounded-xl" data-testid="date-time">
                    <Clock className="mr-2 h-4 w-4 text-[#A8A29E]" />
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TIME_OPTIONS.map(time => (
                      <SelectItem key={time} value={time}>{time}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label className="text-[#57534E]">Duration</Label>
              <Select value={formData.duration} onValueChange={handleSelectChange('duration')}>
                <SelectTrigger className="mt-1.5 rounded-xl" data-testid="date-duration">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1 hour">1 hour</SelectItem>
                  <SelectItem value="2-3 hours">2-3 hours</SelectItem>
                  <SelectItem value="Half day">Half day</SelectItem>
                  <SelectItem value="Full day">Full day</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      )}

      {/* Step 3: Preferences */}
      {step === 3 && (
        <div className="bg-white rounded-2xl border border-stone-200 p-6 animate-slideUp">
          <h2 className="font-semibold text-lg text-[#1C1917] mb-6" style={{ fontFamily: 'Syne, sans-serif' }}>
            Final Details
          </h2>
          
          <div className="space-y-6">
            <div>
              <Label className="text-[#57534E] mb-3 block">Who pays?</Label>
              <div className="grid grid-cols-2 gap-3">
                {WHO_PAYS_OPTIONS.map(opt => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => handleSelectChange('who_pays')(opt.value)}
                    className={`p-4 rounded-xl border-2 text-left transition-all ${
                      formData.who_pays === opt.value
                        ? 'border-[#E76F51] bg-[#E76F51]/5'
                        : 'border-stone-200 hover:border-stone-300'
                    }`}
                    data-testid={`who-pays-${opt.value}`}
                  >
                    <DollarSign className={`w-5 h-5 mb-2 ${
                      formData.who_pays === opt.value ? 'text-[#E76F51]' : 'text-[#A8A29E]'
                    }`} />
                    <p className="font-semibold text-[#1C1917]">{opt.label}</p>
                    <p className="text-xs text-[#57534E]">{opt.description}</p>
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-[#57534E]">Min Age</Label>
                <Input
                  type="number"
                  min="18"
                  max="100"
                  value={formData.age_range_min}
                  onChange={handleChange('age_range_min')}
                  className="mt-1.5 rounded-xl"
                  data-testid="date-age-min"
                />
              </div>
              <div>
                <Label className="text-[#57534E]">Max Age</Label>
                <Input
                  type="number"
                  min="18"
                  max="100"
                  value={formData.age_range_max}
                  onChange={handleChange('age_range_max')}
                  className="mt-1.5 rounded-xl"
                  data-testid="date-age-max"
                />
              </div>
            </div>

            <div>
              <Label className="text-[#57534E]">Max Applications</Label>
              <Select 
                value={formData.max_applicants.toString()} 
                onValueChange={(v) => handleSelectChange('max_applicants')(parseInt(v))}
              >
                <SelectTrigger className="mt-1.5 rounded-xl" data-testid="date-max-applicants">
                  <Users className="mr-2 h-4 w-4 text-[#A8A29E]" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {[5, 10, 15, 20, 25].map(num => (
                    <SelectItem key={num} value={num.toString()}>{num} applicants</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between mt-6">
        <Button
          variant="outline"
          onClick={prevStep}
          disabled={step === 1}
          className="rounded-full"
          data-testid="prev-step-btn"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>

        {step < 3 ? (
          <Button
            onClick={nextStep}
            className="btn-primary rounded-full"
            data-testid="next-step-btn"
          >
            Next
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        ) : (
          <Button
            onClick={handleSubmit}
            disabled={loading}
            className="btn-primary rounded-full"
            data-testid="create-date-btn"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Creating...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Sparkles className="w-4 h-4" />
                Post Date
              </span>
            )}
          </Button>
        )}
      </div>
    </div>
  );
}
