import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import axios from 'axios';
import { 
  Shield, Users, AlertTriangle, Clock, Share2, Phone, Mail, 
  Plus, Trash2, CheckCircle, XCircle, ChevronRight, Bell,
  ShieldCheck, Camera, Smartphone, BadgeCheck, ArrowLeft
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { useAuth } from '../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function SafetyCenterPage() {
  const navigate = useNavigate();
  const { user, trustedContacts, refreshUser, photoVerified, phoneVerified, emailVerified } = useAuth();
  const [contacts, setContacts] = useState([]);
  const [blockedUsers, setBlockedUsers] = useState([]);
  const [newContact, setNewContact] = useState({ name: '', email: '' });
  const [showAddContact, setShowAddContact] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [contactsRes, blockedRes] = await Promise.all([
        axios.get(`${API}/safety/trusted-contacts`),
        axios.get(`${API}/blocked`)
      ]);
      setContacts(contactsRes.data.contacts || []);
      setBlockedUsers(blockedRes.data.blocked || []);
    } catch (error) {
      console.error('Failed to fetch safety data:', error);
    } finally {
      setLoading(false);
    }
  };

  const addTrustedContact = async () => {
    if (!newContact.name || !newContact.email) {
      toast.error('Please fill in all fields');
      return;
    }
    try {
      await axios.post(`${API}/safety/trusted-contacts`, newContact);
      toast.success('Trusted contact added');
      setNewContact({ name: '', email: '' });
      setShowAddContact(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add contact');
    }
  };

  const removeTrustedContact = async (contactId) => {
    try {
      await axios.delete(`${API}/safety/trusted-contacts/${contactId}`);
      toast.success('Contact removed');
      fetchData();
    } catch (error) {
      toast.error('Failed to remove contact');
    }
  };

  const unblockUser = async (userId) => {
    try {
      await axios.delete(`${API}/block/${userId}`);
      toast.success('User unblocked');
      fetchData();
    } catch (error) {
      toast.error('Failed to unblock user');
    }
  };

  return (
    <div className="min-h-screen bg-[#FDFCF8] pb-24">
      {/* Header */}
      <div className="bg-white border-b border-stone-200 sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center gap-3">
          <button onClick={() => navigate(-1)} className="p-2 hover:bg-stone-100 rounded-full">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <Shield className="w-6 h-6 text-[#2A9D8F]" />
            <h1 className="text-xl font-bold" style={{ fontFamily: 'Syne, sans-serif' }}>Safety Center</h1>
          </div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        {/* Safety Promise */}
        <Card className="border-[#2A9D8F]/20 bg-[#2A9D8F]/5">
          <CardContent className="pt-6">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-full bg-[#2A9D8F]/20 flex items-center justify-center flex-shrink-0">
                <ShieldCheck className="w-6 h-6 text-[#2A9D8F]" />
              </div>
              <div>
                <h2 className="font-bold text-lg mb-2" style={{ fontFamily: 'Syne, sans-serif' }}>Our Safety Promise</h2>
                <ul className="text-sm text-[#57534E] space-y-2">
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-[#2A9D8F]" /> Public first dates recommended
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-[#2A9D8F]" /> Verification badges show trust
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-[#2A9D8F]" /> Block & report always available
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-[#2A9D8F]" /> Date check-in keeps you safe
                  </li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Verification Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <BadgeCheck className="w-5 h-5 text-[#E76F51]" />
              Your Verification
            </CardTitle>
            <CardDescription>Verified profiles build more trust</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-stone-100">
              <div className="flex items-center gap-3">
                <Mail className={`w-5 h-5 ${emailVerified ? 'text-[#2A9D8F]' : 'text-stone-300'}`} />
                <span>Email Verified</span>
              </div>
              {emailVerified ? (
                <span className="text-[#2A9D8F] text-sm font-medium flex items-center gap-1">
                  <CheckCircle className="w-4 h-4" /> Verified
                </span>
              ) : (
                <Button size="sm" variant="outline" className="text-[#E76F51] border-[#E76F51]">
                  Verify
                </Button>
              )}
            </div>
            <div className="flex items-center justify-between py-3 border-b border-stone-100">
              <div className="flex items-center gap-3">
                <Camera className={`w-5 h-5 ${photoVerified ? 'text-[#2A9D8F]' : 'text-stone-300'}`} />
                <span>Photo Verified</span>
              </div>
              {photoVerified ? (
                <span className="text-[#2A9D8F] text-sm font-medium flex items-center gap-1">
                  <CheckCircle className="w-4 h-4" /> Verified
                </span>
              ) : (
                <Button 
                  size="sm" 
                  variant="outline" 
                  className="text-[#E76F51] border-[#E76F51]"
                  onClick={() => navigate('/verify/photo')}
                >
                  Verify
                </Button>
              )}
            </div>
            <div className="flex items-center justify-between py-3">
              <div className="flex items-center gap-3">
                <Smartphone className={`w-5 h-5 ${phoneVerified ? 'text-[#2A9D8F]' : 'text-stone-300'}`} />
                <span>Phone Verified</span>
              </div>
              {phoneVerified ? (
                <span className="text-[#2A9D8F] text-sm font-medium flex items-center gap-1">
                  <CheckCircle className="w-4 h-4" /> Verified
                </span>
              ) : (
                <Button 
                  size="sm" 
                  variant="outline" 
                  className="text-[#E76F51] border-[#E76F51]"
                  onClick={() => navigate('/verify/phone')}
                >
                  Verify
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Trusted Contacts */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Users className="w-5 h-5 text-[#E76F51]" />
              Trusted Contacts
            </CardTitle>
            <CardDescription>People who can be notified during date check-ins</CardDescription>
          </CardHeader>
          <CardContent>
            {contacts.length === 0 ? (
              <p className="text-[#A8A29E] text-center py-4">No trusted contacts yet</p>
            ) : (
              <div className="space-y-3 mb-4">
                {contacts.map(contact => (
                  <div key={contact.id} className="flex items-center justify-between p-3 bg-stone-50 rounded-lg">
                    <div>
                      <p className="font-medium">{contact.name}</p>
                      <p className="text-sm text-[#57534E]">{contact.email}</p>
                    </div>
                    <button 
                      onClick={() => removeTrustedContact(contact.id)}
                      className="p-2 text-red-500 hover:bg-red-50 rounded-full"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
            
            <Dialog open={showAddContact} onOpenChange={setShowAddContact}>
              <DialogTrigger asChild>
                <Button 
                  variant="outline" 
                  className="w-full"
                  disabled={contacts.length >= 3}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add Trusted Contact {contacts.length >= 3 && '(Max 3)'}
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Add Trusted Contact</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div>
                    <Label>Name</Label>
                    <Input 
                      value={newContact.name}
                      onChange={e => setNewContact({ ...newContact, name: e.target.value })}
                      placeholder="Friend's name"
                    />
                  </div>
                  <div>
                    <Label>Email</Label>
                    <Input 
                      type="email"
                      value={newContact.email}
                      onChange={e => setNewContact({ ...newContact, email: e.target.value })}
                      placeholder="friend@email.com"
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowAddContact(false)}>Cancel</Button>
                  <Button onClick={addTrustedContact} className="bg-[#E76F51] hover:bg-[#D65D40]">
                    Add Contact
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </CardContent>
        </Card>

        {/* Date Check-In Info */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Clock className="w-5 h-5 text-[#E76F51]" />
              Date Check-In
            </CardTitle>
            <CardDescription>Get reminded to confirm you're safe during dates</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="bg-stone-50 rounded-lg p-4 text-sm text-[#57534E]">
              <p className="mb-3">When you confirm a date plan in chat, you can set up a check-in:</p>
              <ol className="list-decimal list-inside space-y-2">
                <li>Set a check-in time (e.g., 1 hour after date starts)</li>
                <li>If you don't confirm "I'm safe" in time, we'll alert your trusted contacts</li>
                <li>Your contacts receive a generic "please check in" message</li>
              </ol>
            </div>
          </CardContent>
        </Card>

        {/* Blocked Users */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <XCircle className="w-5 h-5 text-red-500" />
              Blocked Users
            </CardTitle>
          </CardHeader>
          <CardContent>
            {blockedUsers.length === 0 ? (
              <p className="text-[#A8A29E] text-center py-4">No blocked users</p>
            ) : (
              <div className="space-y-3">
                {blockedUsers.map(blocked => (
                  <div key={blocked.user_id} className="flex items-center justify-between p-3 bg-stone-50 rounded-lg">
                    <span className="font-medium">{blocked.first_name}</span>
                    <Button 
                      size="sm"
                      variant="outline"
                      onClick={() => unblockUser(blocked.user_id)}
                    >
                      Unblock
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Emergency Resources */}
        <Card className="border-red-200 bg-red-50/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg text-red-700">
              <AlertTriangle className="w-5 h-5" />
              Emergency Resources
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-red-700">
            <p className="mb-3">If you're ever in immediate danger, please contact:</p>
            <ul className="space-y-2">
              <li><strong>Emergency:</strong> 911 (US) / 112 (India)</li>
              <li><strong>National Domestic Violence Hotline:</strong> 1-800-799-7233</li>
              <li><strong>RAINN Sexual Assault Hotline:</strong> 1-800-656-4673</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
