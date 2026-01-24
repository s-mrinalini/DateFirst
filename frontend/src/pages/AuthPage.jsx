import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { toast } from 'sonner';
import { Heart, Mail, Lock, ArrowRight, Eye, EyeOff } from 'lucide-react';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Label } from '../components/ui/label';
import { useAuth } from '../context/AuthContext';

export default function AuthPage() {
  const navigate = useNavigate();
  const { login, signup } = useAuth();
  
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [errors, setErrors] = useState({});

  const validateForm = () => {
    const newErrors = {};
    if (!formData.email) newErrors.email = 'Email is required';
    else if (!/\S+@\S+\.\S+/.test(formData.email)) newErrors.email = 'Invalid email';
    if (!formData.password) newErrors.password = 'Password is required';
    else if (formData.password.length < 6) newErrors.password = 'Min 6 characters';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;
    
    setLoading(true);
    try {
      if (isLogin) {
        const result = await login(formData.email, formData.password);
        toast.success('Welcome back!');
        navigate(result.user.profile_complete ? '/' : '/onboarding');
      } else {
        await signup(formData.email, formData.password);
        toast.success('Account created!');
        navigate('/onboarding');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FDFCF8] flex">
      {/* Left - Form */}
      <div className="flex-1 flex items-center justify-center p-6 lg:p-12">
        <div className="w-full max-w-md animate-slideUp">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-10">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#E76F51] to-[#E9C46A] flex items-center justify-center shadow-lg">
              <Heart className="w-7 h-7 text-white" fill="white" />
            </div>
            <div>
              <span className="font-bold text-2xl text-[#1C1917] block" style={{ fontFamily: 'Syne, sans-serif' }}>
                DateFirst
              </span>
              <span className="text-xs text-[#57534E]">Ideas before profiles</span>
            </div>
          </div>

          <h1 className="text-3xl font-bold text-[#1C1917] mb-2" style={{ fontFamily: 'Syne, sans-serif' }}>
            {isLogin ? 'Welcome back' : 'Join DateFirst'}
          </h1>
          <p className="text-[#57534E] mb-8">
            {isLogin ? 'Sign in to discover amazing date ideas' : 'Create your account and share your perfect first date'}
          </p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <Label className="text-[#1C1917] font-medium">Email</Label>
              <div className="relative mt-1.5">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#A8A29E]" />
                <Input
                  type="email"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className={`pl-10 rounded-xl h-12 ${errors.email ? 'border-red-500' : ''}`}
                  data-testid="auth-email"
                />
              </div>
              {errors.email && <p className="text-red-500 text-sm mt-1">{errors.email}</p>}
            </div>

            <div>
              <Label className="text-[#1C1917] font-medium">Password</Label>
              <div className="relative mt-1.5">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#A8A29E]" />
                <Input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className={`pl-10 pr-10 rounded-xl h-12 ${errors.password ? 'border-red-500' : ''}`}
                  data-testid="auth-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#A8A29E]"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {errors.password && <p className="text-red-500 text-sm mt-1">{errors.password}</p>}
            </div>

            <Button
              type="submit"
              className="w-full h-12 bg-[#E76F51] hover:bg-[#D65D40] rounded-xl text-base font-semibold"
              disabled={loading}
              data-testid="auth-submit"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  {isLogin ? 'Signing in...' : 'Creating account...'}
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  {isLogin ? 'Sign in' : 'Create account'}
                  <ArrowRight className="w-5 h-5" />
                </span>
              )}
            </Button>
          </form>

          <p className="text-center mt-6 text-[#57534E]">
            {isLogin ? "Don't have an account?" : 'Already have an account?'}
            {' '}
            <button
              onClick={() => { setIsLogin(!isLogin); setErrors({}); }}
              className="text-[#E76F51] font-semibold hover:underline"
              data-testid="toggle-auth"
            >
              {isLogin ? 'Sign up' : 'Sign in'}
            </button>
          </p>

          <div className="mt-8 p-4 bg-stone-100 rounded-xl text-sm">
            <p className="font-medium text-[#1C1917] mb-1">Demo accounts:</p>
            <p className="text-[#57534E]">emma@example.com / password123</p>
          </div>
        </div>
      </div>

      {/* Right - Image */}
      <div className="hidden lg:block lg:w-1/2 relative">
        <div 
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1516589178581-6cd7833ae3b2?w=1200)' }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#1C1917]/80 via-transparent to-transparent" />
        <div className="absolute bottom-0 left-0 right-0 p-12">
          <p className="text-2xl text-white font-medium mb-4" style={{ fontFamily: 'Syne, sans-serif' }}>
            "Browse date ideas, not just faces."
          </p>
          <p className="text-white/70">Match on experiences that excite you both.</p>
        </div>
      </div>
    </div>
  );
}
