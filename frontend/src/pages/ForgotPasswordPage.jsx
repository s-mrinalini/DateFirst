import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { Heart, Mail, ArrowLeft } from 'lucide-react';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Label } from '../components/ui/label';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !/\S+@\S+\.\S+/.test(email)) {
      toast.error('Enter a valid email');
      return;
    }
    setLoading(true);
    try {
      await axios.post(`${API}/auth/forgot-password`, { email });
      setSubmitted(true);
    } catch (err) {
      // Backend always returns 200 to avoid email enumeration; surface real network errors only.
      toast.error('Could not reach the server. Try again.');
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
          Forgot your password?
        </h1>
        <p className="text-[#57534E] mb-6">
          Enter your email and we'll send you a link to set a new one.
        </p>

        {submitted ? (
          <div className="bg-stone-100 rounded-xl p-6 text-[#1C1917]">
            <p className="font-medium mb-2">Check your inbox.</p>
            <p className="text-sm text-[#57534E]">
              If <span className="font-medium">{email}</span> is registered, a reset link is on
              its way. The link is valid for 30 minutes.
            </p>
            <Link
              to="/auth"
              className="mt-4 inline-flex items-center gap-1 text-[#E76F51] font-medium"
            >
              <ArrowLeft className="w-4 h-4" /> Back to sign in
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <Label className="text-[#1C1917] font-medium">Email</Label>
              <div className="relative mt-1.5">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#A8A29E]" />
                <Input
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-10 rounded-xl h-12"
                  data-testid="forgot-email"
                />
              </div>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full h-12 bg-[#E76F51] hover:bg-[#D65D40] rounded-xl text-base font-semibold"
              data-testid="forgot-submit"
            >
              {loading ? 'Sending...' : 'Send reset link'}
            </Button>

            <Link
              to="/auth"
              className="flex items-center justify-center gap-1 text-[#57534E] hover:text-[#E76F51] mt-2"
            >
              <ArrowLeft className="w-4 h-4" /> Back to sign in
            </Link>
          </form>
        )}
      </div>
    </div>
  );
}
