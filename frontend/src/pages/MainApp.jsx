import React, { useState } from 'react';
import { Routes, Route, useLocation, Link } from 'react-router-dom';
import { Compass, Heart, MessageCircle, User } from 'lucide-react';
import DiscoverPage from './DiscoverPage';
import VibesPage from './VibesPage';
import PlansPage from './PlansPage';
import ChatPage from './ChatPage';
import ProfilePage from './ProfilePage';
import SettingsPage from './SettingsPage';

const TABS = [
  { path: '/', icon: Compass, label: 'Discover' },
  { path: '/vibes', icon: Heart, label: 'Vibes' },
  { path: '/plans', icon: MessageCircle, label: 'Plans' },
  { path: '/profile', icon: User, label: 'Profile' },
];

export default function MainApp() {
  const location = useLocation();
  const isChat = location.pathname.startsWith('/chat/');
  
  const getActiveTab = () => {
    if (location.pathname === '/') return '/';
    if (location.pathname.startsWith('/vibes')) return '/vibes';
    if (location.pathname.startsWith('/plans') || location.pathname.startsWith('/chat')) return '/plans';
    if (location.pathname.startsWith('/profile') || location.pathname.startsWith('/settings')) return '/profile';
    return '/';
  };
  
  const activeTab = getActiveTab();

  return (
    <div className="min-h-screen bg-[#FDFCF8] pb-20">
      {/* Main Content */}
      <Routes>
        <Route path="/" element={<DiscoverPage />} />
        <Route path="/vibes" element={<VibesPage />} />
        <Route path="/plans" element={<PlansPage />} />
        <Route path="/chat/:threadId" element={<ChatPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>

      {/* Bottom Tab Bar */}
      {!isChat && (
        <nav className="fixed bottom-0 left-0 right-0 bg-white/95 backdrop-blur-lg border-t border-stone-200 px-4 pb-safe z-50">
          <div className="flex justify-around items-center h-16 max-w-lg mx-auto">
            {TABS.map(({ path, icon: Icon, label }) => {
              const isActive = activeTab === path;
              return (
                <Link
                  key={path}
                  to={path}
                  className={`flex flex-col items-center gap-1 py-2 px-4 rounded-xl transition-all ${
                    isActive ? 'text-[#E76F51]' : 'text-[#A8A29E] hover:text-[#57534E]'
                  }`}
                  data-testid={`nav-${label.toLowerCase()}`}
                >
                  <Icon 
                    className={`w-6 h-6 ${isActive ? '' : ''}`} 
                    fill={isActive && label === 'Vibes' ? 'currentColor' : 'none'}
                  />
                  <span className="text-xs font-medium">{label}</span>
                </Link>
              );
            })}
          </div>
        </nav>
      )}
    </div>
  );
}
