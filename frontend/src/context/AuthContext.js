import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
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
    
    // Fetch full profile
    await fetchUser();
    
    return response.data;
  };

  const signup = async (email, password, firstName) => {
    const response = await axios.post(`${API}/auth/signup`, {
      email,
      password,
      first_name: firstName,
    });
    const { token: newToken, user: userData } = response.data;
    
    localStorage.setItem('token', newToken);
    axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
    setToken(newToken);
    setUser(userData);
    
    // Fetch full profile
    await fetchUser();
    
    return response.data;
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setToken(null);
    setUser(null);
    setProfile(null);
  };

  const updateProfile = async (data) => {
    const response = await axios.put(`${API}/profile`, data);
    setProfile(response.data);
    if (data.first_name) {
      setUser(prev => ({ ...prev, first_name: data.first_name }));
    }
    return response.data;
  };

  const upgradeToPremium = async () => {
    const response = await axios.post(`${API}/upgrade`);
    setUser(prev => ({ ...prev, is_premium: true }));
    return response.data;
  };

  const value = {
    user,
    profile,
    loading,
    isAuthenticated: !!user,
    isPremium: user?.is_premium || false,
    login,
    signup,
    logout,
    updateProfile,
    upgradeToPremium,
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
