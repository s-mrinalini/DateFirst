import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { ArrowLeft, Shield, Ban, LogOut, Trash2, ChevronRight } from 'lucide-react';
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
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [blockedUsers, setBlockedUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [unblockId, setUnblockId] = useState(null);

  useEffect(() => {
    fetchBlocked();
  }, []);

  const fetchBlocked = async () => {
    try {
      const response = await axios.get(`${API}/blocked`);
      setBlockedUsers(response.data.blocked);
    } catch (error) {
      console.error('Failed to load blocked users');
    } finally {
      setLoading(false);
    }
  };

  const handleUnblock = async () => {
    if (!unblockId) return;
    try {
      await axios.delete(`${API}/block/${unblockId}`);
      setBlockedUsers(prev => prev.filter(u => u.user_id !== unblockId));
      toast.success('User unblocked');
    } catch (error) {
      toast.error('Failed to unblock');
    } finally {
      setUnblockId(null);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/auth');
  };

  return (
    <div className="min-h-screen bg-[#FDFCF8] p-4 pb-24">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <button 
          onClick={() => navigate('/profile')}
          className="p-2 -ml-2 hover:bg-stone-100 rounded-full"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-2xl font-bold text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
          Settings
        </h1>
      </div>

      {/* Blocked Users */}
      <div className="bg-white rounded-2xl shadow-sm overflow-hidden mb-6">
        <div className="p-4 border-b border-stone-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#E76F51]/10 flex items-center justify-center">
              <Ban className="w-5 h-5 text-[#E76F51]" />
            </div>
            <div>
              <h3 className="font-semibold text-[#1C1917]">Blocked Users</h3>
              <p className="text-xs text-[#57534E]">{blockedUsers.length} blocked</p>
            </div>
          </div>
        </div>

        {blockedUsers.length > 0 ? (
          <div className="divide-y divide-stone-100">
            {blockedUsers.map(user => (
              <div 
                key={user.user_id}
                className="p-4 flex items-center justify-between"
              >
                <span className="font-medium">{user.first_name}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setUnblockId(user.user_id)}
                  className="text-[#E76F51]"
                  data-testid={`unblock-${user.user_id}`}
                >
                  Unblock
                </Button>
              </div>
            ))}
          </div>
        ) : (
          <p className="p-4 text-sm text-[#A8A29E] text-center">No blocked users</p>
        )}
      </div>

      {/* Account Actions */}
      <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
        <button
          onClick={handleLogout}
          className="w-full p-4 flex items-center justify-between hover:bg-stone-50 transition-colors"
          data-testid="logout-btn"
        >
          <div className="flex items-center gap-3">
            <LogOut className="w-5 h-5 text-[#57534E]" />
            <span className="text-[#1C1917]">Log out</span>
          </div>
          <ChevronRight className="w-5 h-5 text-[#A8A29E]" />
        </button>

        <div className="border-t border-stone-100">
          <button
            className="w-full p-4 flex items-center justify-between hover:bg-red-50 transition-colors"
            data-testid="delete-account-btn"
          >
            <div className="flex items-center gap-3">
              <Trash2 className="w-5 h-5 text-red-500" />
              <span className="text-red-500">Delete Account</span>
            </div>
            <ChevronRight className="w-5 h-5 text-red-300" />
          </button>
        </div>
      </div>

      {/* App Info */}
      <div className="mt-8 text-center text-sm text-[#A8A29E]">
        <p>DateFirst v2.0</p>
        <p className="mt-1">Ideas before profiles ❤️</p>
      </div>

      {/* Unblock Dialog */}
      <AlertDialog open={!!unblockId} onOpenChange={() => setUnblockId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Unblock user?</AlertDialogTitle>
            <AlertDialogDescription>
              They'll be able to see your profile again.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="rounded-full">Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleUnblock}
              className="rounded-full"
            >
              Unblock
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
