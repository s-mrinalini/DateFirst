import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [trustedContacts, setTrustedContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data.user);
      setProfile(response.data.profile);
      setTrustedContacts(response.data.trusted_contacts || []);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password });
    const { token: newToken, user: userData } = response.data;
    
    localStorage.setItem('token', newToken);
    axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
    setToken(newToken);
    setUser(userData);
    
    await fetchUser();
    return response.data;
  };

  const signup = async (email, password) => {
    const response = await axios.post(`${API}/auth/signup`, { email, password });
    const { token: newToken, user: userData } = response.data;
    
    localStorage.setItem('token', newToken);
    axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
    setToken(newToken);
    setUser(userData);
    
    return response.data;
  };

  const verifyEmail = async (code) => {
    const response = await axios.post(`${API}/auth/verify-email`, { code });
    setUser(prev => ({ ...prev, email_verified: true }));
    return response.data;
  };

  const resendVerification = async () => {
    const response = await axios.post(`${API}/auth/resend-verification`);
    return response.data;
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`);
    } catch (e) {
      // Ignore errors
    }
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setToken(null);
    setUser(null);
    setProfile(null);
    setTrustedContacts([]);
  };

  const logoutAllDevices = async () => {
    const response = await axios.post(`${API}/auth/logout-all`);
    logout();
    return response.data;
  };

  const setupProfile = async (data) => {
    const response = await axios.post(`${API}/profile/setup`, data);
    setProfile(response.data.profile);
    setUser(prev => ({ ...prev, profile_complete: true }));
    return response.data;
  };

  const updateProfile = async (data) => {
    const response = await axios.put(`${API}/profile`, data);
    setProfile(response.data);
    return response.data;
  };

  const value = {
    user,
    profile,
    trustedContacts,
    loading,
    isAuthenticated: !!user,
    profileComplete: user?.profile_complete || false,
    emailVerified: user?.email_verified || false,
    photoVerified: user?.photo_verified || false,
    phoneVerified: user?.phone_verified || false,
    badges: user?.badges || [],
    login,
    signup,
    verifyEmail,
    resendVerification,
    logout,
    logoutAllDevices,
    setupProfile,
    updateProfile,
    refreshUser: fetchUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
