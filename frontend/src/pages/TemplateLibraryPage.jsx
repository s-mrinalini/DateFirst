import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import axios from 'axios';
import { 
  Search, Filter, MapPin, Clock, DollarSign, Heart, Sparkles,
  ChevronDown, X, ArrowLeft, Shield, Coffee, Utensils, TreePine,
  Palette, Gamepad2, Sofa, Sun
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { useAuth } from '../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CATEGORY_ICONS = {
  coffee: Coffee,
  food: Utensils,
  outdoors: TreePine,
  culture: Palette,
  activities: Gamepad2,
  cozy: Sofa,
  daytime: Sun
};

export default function TemplateLibraryPage() {
  const navigate = useNavigate();
  const { profile } = useAuth();
  const [templates, setTemplates] = useState([]);
  const [cities, setCities] = useState([]);
  const [favorites, setFavorites] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [selectedCity, setSelectedCity] = useState(profile?.city || '');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('all');
  const [filters, setFilters] = useState({
    safety_level: '',
    cost_hint: '',
    place_type: ''
  });

  useEffect(() => {
    fetchCities();
    fetchFavorites();
  }, []);

  useEffect(() => {
    fetchTemplates();
  }, [selectedCity, searchQuery, filters]);

  const fetchCities = async () => {
    try {
      const response = await axios.get(`${API}/templates/cities`);
      setCities(response.data.cities || []);
    } catch (error) {
      console.error('Failed to fetch cities:', error);
    }
  };

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedCity) params.append('city', selectedCity);
      if (searchQuery) params.append('search', searchQuery);
      if (filters.safety_level) params.append('safety_level', filters.safety_level);
      if (filters.cost_hint) params.append('cost_hint', filters.cost_hint);
      params.append('limit', '100');
      
      const response = await axios.get(`${API}/templates?${params.toString()}`);
      setTemplates(response.data.templates || []);
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFavorites = async () => {
    try {
      const response = await axios.get(`${API}/templates/favorites`);
      const favIds = new Set(response.data.favorites.map(f => f.id));
      setFavorites(favIds);
    } catch (error) {
      console.error('Failed to fetch favorites:', error);
    }
  };

  const toggleFavorite = async (templateId) => {
    try {
      await axios.post(`${API}/templates/${templateId}/favorite`);
      setFavorites(prev => {
        const newFavs = new Set(prev);
        if (newFavs.has(templateId)) {
          newFavs.delete(templateId);
        } else {
          newFavs.add(templateId);
        }
        return newFavs;
      });
    } catch (error) {
      toast.error('Failed to update favorite');
    }
  };

  const surpriseMe = async () => {
    try {
      const response = await axios.get(`${API}/templates/suggest?surprise_me=true&city=${selectedCity}`);
      if (response.data.suggestions?.length > 0) {
        const suggestion = response.data.suggestions[0];
        toast.success(`Try: ${suggestion.title}`, { duration: 5000 });
      }
    } catch (error) {
      toast.error('No suggestions available');
    }
  };

  const handleUseTemplate = (template) => {
    // Navigate to onboarding/edit with template data
    navigate('/onboarding', { 
      state: { 
        templateData: {
          title: template.title,
          description: template.description,
          tags: template.tags,
          is_public_meetup: template.safety_level?.includes('Public'),
          suggested_meetup: template.suggested_meetup_type
        }
      }
    });
  };

  const globalTemplates = templates.filter(t => t.is_global);
  const cityTemplates = templates.filter(t => !t.is_global);
  const favoriteTemplates = templates.filter(t => favorites.has(t.id));

  const filteredTemplates = activeTab === 'favorites' 
    ? favoriteTemplates 
    : activeTab === 'city' 
      ? cityTemplates 
      : activeTab === 'global' 
        ? globalTemplates 
        : templates;

  return (
    <div className="min-h-screen bg-[#FDFCF8] pb-24">
      {/* Header */}
      <div className="bg-white border-b border-stone-200 sticky top-0 z-20">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3 mb-4">
            <button onClick={() => navigate(-1)} className="p-2 hover:bg-stone-100 rounded-full">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-xl font-bold" style={{ fontFamily: 'Syne, sans-serif' }}>Date Ideas Library</h1>
              <p className="text-sm text-[#57534E]">Find the perfect first date idea</p>
            </div>
          </div>
          
          {/* City Selector & Search */}
          <div className="flex gap-3 mb-4">
            <Select value={selectedCity} onValueChange={setSelectedCity}>
              <SelectTrigger className="w-48">
                <MapPin className="w-4 h-4 mr-2 text-[#E76F51]" />
                <SelectValue placeholder="Select city" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">All Cities</SelectItem>
                {cities.map(city => (
                  <SelectItem key={city.name} value={city.name}>
                    {city.name} ({city.template_count})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#A8A29E]" />
              <Input
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Search templates..."
                className="pl-10"
              />
            </div>
            
            <Button 
              variant="outline" 
              onClick={surpriseMe}
              className="border-[#E76F51] text-[#E76F51] hover:bg-[#E76F51]/10"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              Surprise Me
            </Button>
          </div>

          {/* Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="w-full bg-stone-100">
              <TabsTrigger value="all" className="flex-1">All ({templates.length})</TabsTrigger>
              {selectedCity && (
                <TabsTrigger value="city" className="flex-1">
                  Iconic ({cityTemplates.length})
                </TabsTrigger>
              )}
              <TabsTrigger value="global" className="flex-1">Classic ({globalTemplates.length})</TabsTrigger>
              <TabsTrigger value="favorites" className="flex-1">
                <Heart className="w-4 h-4 mr-1" />
                ({favoriteTemplates.length})
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </div>

      {/* Filters */}
      <div className="max-w-4xl mx-auto px-4 py-3 flex gap-2 flex-wrap">
        <Select value={filters.safety_level} onValueChange={v => setFilters({...filters, safety_level: v})}>
          <SelectTrigger className="w-40 h-9 text-sm">
            <Shield className="w-3 h-3 mr-1" />
            <SelectValue placeholder="Safety" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__any__">Any Safety</SelectItem>
            <SelectItem value="Public & Busy">Public &amp; Busy</SelectItem>
            <SelectItem value="Public & Calm">Public &amp; Calm</SelectItem>
          </SelectContent>
        </Select>
        
        <Select value={filters.cost_hint} onValueChange={v => setFilters({...filters, cost_hint: v})}>
          <SelectTrigger className="w-32 h-9 text-sm">
            <DollarSign className="w-3 h-3 mr-1" />
            <SelectValue placeholder="Cost" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__any__">Any Cost</SelectItem>
            <SelectItem value="Free">Free</SelectItem>
            <SelectItem value="$">$</SelectItem>
            <SelectItem value="$$">$$</SelectItem>
          </SelectContent>
        </Select>
        
        {(filters.safety_level && filters.safety_level !== '__any__' || filters.cost_hint && filters.cost_hint !== '__any__') && (
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => setFilters({ safety_level: '__any__', cost_hint: '__any__', place_type: '' })}
            className="text-[#A8A29E]"
          >
            <X className="w-3 h-3 mr-1" />
            Clear
          </Button>
        )}
      </div>

      {/* Templates Grid */}
      <div className="max-w-4xl mx-auto px-4 py-4">
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1,2,3,4].map(i => (
              <div key={i} className="h-48 bg-stone-100 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : filteredTemplates.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-[#A8A29E]">No templates found</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredTemplates.map(template => (
              <Card 
                key={template.id} 
                className="overflow-hidden hover:shadow-lg transition-all cursor-pointer group"
                data-testid={`template-card-${template.id}`}
              >
                <CardContent className="p-5">
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex-1">
                      <h3 className="font-bold text-[#1C1917] group-hover:text-[#E76F51] transition-colors" style={{ fontFamily: 'Syne, sans-serif' }}>
                        {template.title}
                      </h3>
                      {template.city && (
                        <span className="text-xs text-[#E76F51] font-medium flex items-center gap-1 mt-1">
                          <MapPin className="w-3 h-3" />
                          {template.city} {template.locality_label && `• ${template.locality_label}`}
                        </span>
                      )}
                    </div>
                    <button 
                      onClick={(e) => { e.stopPropagation(); toggleFavorite(template.id); }}
                      className="p-2 hover:bg-stone-100 rounded-full"
                    >
                      <Heart 
                        className={`w-5 h-5 ${favorites.has(template.id) ? 'fill-[#E76F51] text-[#E76F51]' : 'text-stone-300'}`} 
                      />
                    </button>
                  </div>
                  
                  <p className="text-sm text-[#57534E] mb-4 line-clamp-2">{template.description}</p>
                  
                  {/* Tags */}
                  <div className="flex flex-wrap gap-1.5 mb-4">
                    {template.tags?.slice(0, 4).map(tag => (
                      <Badge key={tag} variant="secondary" className="text-xs bg-stone-100 text-[#57534E]">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                  
                  {/* Meta */}
                  <div className="flex items-center gap-4 text-xs text-[#A8A29E] mb-4">
                    {template.safety_level && (
                      <span className="flex items-center gap-1">
                        <Shield className={`w-3 h-3 ${template.safety_level.includes('Busy') ? 'text-[#2A9D8F]' : 'text-[#E9C46A]'}`} />
                        {template.safety_level}
                      </span>
                    )}
                    {template.cost_hint && (
                      <span className="flex items-center gap-1">
                        <DollarSign className="w-3 h-3" />
                        {template.cost_hint}
                      </span>
                    )}
                    {template.duration_hint && (
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {template.duration_hint}
                      </span>
                    )}
                  </div>
                  
                  <Button 
                    onClick={() => handleUseTemplate(template)}
                    className="w-full bg-[#E76F51] hover:bg-[#D65D40]"
                    data-testid={`use-template-${template.id}`}
                  >
                    Use This Template
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
