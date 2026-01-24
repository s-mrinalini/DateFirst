import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import axios from 'axios';
import { 
  Shield, 
  Ban, 
  Trash2, 
  ChevronRight,
  AlertTriangle
} from 'lucide-react';
import { Button } from '../components/ui/button';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../components/ui/alert-dialog';
import { useAuth } from '../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function SettingsPage() {
  const { logout } = useAuth();
  const [blockedUsers, setBlockedUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [unblockId, setUnblockId] = useState(null);

  useEffect(() => {
    fetchBlockedUsers();
  }, []);

  const fetchBlockedUsers = async () => {
    try {
      const response = await axios.get(`${API}/blocked-users`);
      setBlockedUsers(response.data);
    } catch (error) {
      toast.error('Failed to load blocked users');
    } finally {
      setLoading(false);
    }
  };

  const handleUnblock = async () => {
    if (!unblockId) return;
    
    try {
      await axios.delete(`${API}/block/${unblockId}`);
      setBlockedUsers(prev => prev.filter(u => u.id !== unblockId));
      toast.success('User unblocked');
    } catch (error) {
      toast.error('Failed to unblock user');
    } finally {
      setUnblockId(null);
    }
  };

  return (
    <div className="max-w-2xl mx-auto animate-fadeIn">
      <h1 
        className="text-2xl sm:text-3xl font-bold text-[#1C1917] mb-8"
        style={{ fontFamily: 'Syne, sans-serif' }}
      >
        Settings
      </h1>

      {/* Safety & Privacy */}
      <div className="bg-white rounded-2xl border border-stone-200 overflow-hidden mb-6">
        <div className="p-5 border-b border-stone-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#2A9D8F]/10 flex items-center justify-center">
              <Shield className="w-5 h-5 text-[#2A9D8F]" />
            </div>
            <div>
              <h2 className="font-semibold text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
                Safety & Privacy
              </h2>
              <p className="text-sm text-[#57534E]">Manage your blocked users</p>
            </div>
          </div>
        </div>

        <div className="p-5">
          <h3 className="text-sm font-medium text-[#57534E] mb-4 flex items-center gap-2">
            <Ban className="w-4 h-4" />
            Blocked Users ({blockedUsers.length})
          </h3>

          {loading ? (
            <div className="space-y-3">
              {[...Array(2)].map((_, i) => (
                <div key={i} className="h-12 skeleton rounded-xl" />
              ))}
            </div>
          ) : blockedUsers.length > 0 ? (
            <div className="space-y-2">
              {blockedUsers.map((user) => (
                <div 
                  key={user.id}
                  className="flex items-center justify-between p-3 bg-[#FDFCF8] rounded-xl"
                >
                  <span className="font-medium text-[#1C1917]">{user.first_name}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setUnblockId(user.id)}
                    className="text-[#E76F51] hover:text-[#D65D40]"
                    data-testid={`unblock-btn-${user.id}`}
                  >
                    Unblock
                  </Button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-[#A8A29E] text-center py-4">
              No blocked users
            </p>
          )}
        </div>
      </div>

      {/* Account */}
      <div className="bg-white rounded-2xl border border-stone-200 overflow-hidden">
        <div className="p-5 border-b border-stone-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-stone-100 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-[#57534E]" />
            </div>
            <div>
              <h2 className="font-semibold text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
                Account
              </h2>
              <p className="text-sm text-[#57534E]">Manage your account</p>
            </div>
          </div>
        </div>

        <div className="p-5 space-y-2">
          <button 
            onClick={logout}
            className="w-full flex items-center justify-between p-3 rounded-xl hover:bg-[#FDFCF8] transition-colors text-left"
            data-testid="logout-btn"
          >
            <span className="text-[#1C1917]">Log out</span>
            <ChevronRight className="w-5 h-5 text-[#A8A29E]" />
          </button>
          
          <button 
            className="w-full flex items-center justify-between p-3 rounded-xl hover:bg-red-50 transition-colors text-left group"
            data-testid="delete-account-btn"
          >
            <span className="text-red-500 group-hover:text-red-600">Delete Account</span>
            <Trash2 className="w-5 h-5 text-red-400 group-hover:text-red-500" />
          </button>
        </div>
      </div>

      {/* App Info */}
      <div className="mt-8 text-center text-sm text-[#A8A29E]">
        <p>DateFirst v1.0.0</p>
        <p className="mt-1">Made with love for meaningful connections</p>
      </div>

      {/* Unblock Dialog */}
      <AlertDialog open={!!unblockId} onOpenChange={() => setUnblockId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Unblock this user?</AlertDialogTitle>
            <AlertDialogDescription>
              They'll be able to see your profile and dates again.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="rounded-full">Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleUnblock}
              className="rounded-full"
              data-testid="confirm-unblock-btn"
            >
              Unblock
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
