import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { Heart, Lock, Eye, EyeOff } from 'lucide-react';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Label } from '../components/ui/label';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function ResetPasswordPage() {
  const { token } = useParams();
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }
    if (password !== confirm) {
      toast.error('Passwords do not match');
      return;
    }
    setLoading(true);
    try {
      await axios.post(`${API}/auth/reset-password`, { token, new_password: password });
      toast.success('Password reset. Please sign in.');
      navigate('/auth');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Could not reset password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FDFCF8] flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#E76F51] to-[#E9C46A] flex items-center justify-center shadow-lg">
            <Heart className="w-6 h-6 text-white" fill="white" />
          </div>
          <span className="font-bold text-xl text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
            DateFirst
          </span>
        </div>

        <h1 className="text-2xl font-bold text-[#1C1917] mb-2" style={{ fontFamily: 'Syne, sans-serif' }}>
          Set a new password
        </h1>
        <p className="text-[#57534E] mb-6">Pick something strong (at least 8 characters).</p>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <Label className="text-[#1C1917] font-medium">New password</Label>
            <div className="relative mt-1.5">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#A8A29E]" />
              <Input
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pl-10 pr-10 rounded-xl h-12"
                data-testid="reset-password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#A8A29E]"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          <div>
            <Label className="text-[#1C1917] font-medium">Confirm password</Label>
            <div className="relative mt-1.5">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#A8A29E]" />
              <Input
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                className="pl-10 rounded-xl h-12"
                data-testid="reset-confirm"
              />
            </div>
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="w-full h-12 bg-[#E76F51] hover:bg-[#D65D40] rounded-xl text-base font-semibold"
            data-testid="reset-submit"
          >
            {loading ? 'Resetting...' : 'Reset password'}
          </Button>

          <p className="text-center text-[#57534E]">
            Remembered it?{' '}
            <Link to="/auth" className="text-[#E76F51] font-semibold hover:underline">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
