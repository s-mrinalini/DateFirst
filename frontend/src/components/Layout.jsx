import React from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { formatName } from '../lib/displayName';
import { 
  Home, 
  PlusCircle, 
  MessageCircle, 
  User, 
  Calendar,
  Settings,
  LogOut,
  Heart,
  Crown,
  Menu,
  X,
  FileText
} from 'lucide-react';
import { Button } from './ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';

export const Layout = () => {
  const { user, profile, isAuthenticated, isPremium, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  const isActive = (path) => location.pathname === path;

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen pb-20 md:pb-0">
      {/* Desktop Header */}
      <header className="hidden md:block sticky top-0 z-40 glass border-b border-stone-200/50">
        <div className="container-app">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2">
              <div className="w-10 h-10 rounded-xl bg-[#E76F51] flex items-center justify-center">
                <Heart className="w-5 h-5 text-white" fill="white" />
              </div>
              <span className="font-bold text-xl text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
                DateFirst
              </span>
            </Link>

            {/* Nav Links */}
            <nav className="flex items-center gap-1">
              <Link
                to="/"
                className={`nav-link ${isActive('/') ? 'active' : ''}`}
              >
                Browse
              </Link>
              {isAuthenticated && (
                <>
                  <Link
                    to="/my-dates"
                    className={`nav-link ${isActive('/my-dates') ? 'active' : ''}`}
                  >
                    My Dates
                  </Link>
                  <Link
                    to="/my-applications"
                    className={`nav-link ${isActive('/my-applications') ? 'active' : ''}`}
                  >
                    Applications
                  </Link>
                  <Link
                    to="/chat"
                    className={`nav-link ${isActive('/chat') ? 'active' : ''}`}
                  >
                    Messages
                  </Link>
                </>
              )}
            </nav>

            {/* Actions */}
            <div className="flex items-center gap-3">
              {isAuthenticated ? (
                <>
                  <Link to="/dates/new">
                    <Button 
                      className="btn-primary rounded-full px-5 flex items-center gap-2"
                      data-testid="post-date-btn"
                    >
                      <PlusCircle className="w-4 h-4" />
                      Post a Date
                    </Button>
                  </Link>

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <button className="flex items-center gap-2 p-1 rounded-full hover:bg-stone-100 transition-colors" data-testid="user-menu-btn">
                        <Avatar className="w-9 h-9 border-2 border-white shadow-sm">
                          <AvatarImage src={profile?.profile_photo} />
                          <AvatarFallback className="bg-[#2A9D8F] text-white text-sm font-medium">
                            {user?.first_name?.[0]?.toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                        {isPremium && (
                          <Crown className="w-4 h-4 text-[#E9C46A]" fill="#E9C46A" />
                        )}
                      </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-56">
                      <div className="px-3 py-2">
                        <p className="font-semibold text-[#1C1917]">{formatName(user)}</p>
                        <p className="text-sm text-[#57534E]">{user?.email}</p>
                      </div>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => navigate('/profile')} data-testid="profile-menu-item">
                        <User className="w-4 h-4 mr-2" />
                        Profile
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => navigate('/my-dates')} data-testid="my-dates-menu-item">
                        <Calendar className="w-4 h-4 mr-2" />
                        My Dates
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => navigate('/my-applications')} data-testid="my-apps-menu-item">
                        <FileText className="w-4 h-4 mr-2" />
                        My Applications
                      </DropdownMenuItem>
                      {!isPremium && (
                        <DropdownMenuItem onClick={() => navigate('/upgrade')} className="text-[#E76F51]" data-testid="upgrade-menu-item">
                          <Crown className="w-4 h-4 mr-2" />
                          Upgrade to Premium
                        </DropdownMenuItem>
                      )}
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => navigate('/settings')} data-testid="settings-menu-item">
                        <Settings className="w-4 h-4 mr-2" />
                        Settings
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={handleLogout} className="text-red-600" data-testid="logout-menu-item">
                        <LogOut className="w-4 h-4 mr-2" />
                        Log out
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </>
              ) : (
                <Link to="/auth">
                  <Button className="btn-primary rounded-full px-6" data-testid="login-btn">
                    Sign In
                  </Button>
                </Link>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Header */}
      <header className="md:hidden sticky top-0 z-40 glass border-b border-stone-200/50">
        <div className="flex items-center justify-between h-14 px-4">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[#E76F51] flex items-center justify-center">
              <Heart className="w-4 h-4 text-white" fill="white" />
            </div>
            <span className="font-bold text-lg text-[#1C1917]" style={{ fontFamily: 'Syne, sans-serif' }}>
              DateFirst
            </span>
          </Link>

          {isAuthenticated ? (
            <div className="flex items-center gap-2">
              <Link to="/dates/new">
                <Button size="sm" className="btn-primary rounded-full px-4" data-testid="mobile-post-btn">
                  <PlusCircle className="w-4 h-4" />
                </Button>
              </Link>
              <button 
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-2"
                data-testid="mobile-menu-toggle"
              >
                {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>
          ) : (
            <Link to="/auth">
              <Button size="sm" className="btn-primary rounded-full px-4" data-testid="mobile-login-btn">
                Sign In
              </Button>
            </Link>
          )}
        </div>

        {/* Mobile Menu Dropdown */}
        {mobileMenuOpen && isAuthenticated && (
          <div className="absolute top-full left-0 right-0 bg-white border-b border-stone-200 shadow-lg animate-slideDown">
            <div className="p-4 border-b border-stone-100">
              <div className="flex items-center gap-3">
                <Avatar className="w-12 h-12">
                  <AvatarImage src={profile?.profile_photo} />
                  <AvatarFallback className="bg-[#2A9D8F] text-white">
                    {user?.first_name?.[0]?.toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-semibold">{formatName(user)}</p>
                  <p className="text-sm text-[#57534E]">{user?.email}</p>
                </div>
                {isPremium && <Crown className="w-5 h-5 text-[#E9C46A]" fill="#E9C46A" />}
              </div>
            </div>
            <nav className="py-2">
              <Link 
                to="/profile" 
                className="flex items-center gap-3 px-4 py-3 hover:bg-stone-50"
                onClick={() => setMobileMenuOpen(false)}
              >
                <User className="w-5 h-5 text-[#57534E]" />
                <span>Profile</span>
              </Link>
              <Link 
                to="/my-dates" 
                className="flex items-center gap-3 px-4 py-3 hover:bg-stone-50"
                onClick={() => setMobileMenuOpen(false)}
              >
                <Calendar className="w-5 h-5 text-[#57534E]" />
                <span>My Dates</span>
              </Link>
              <Link 
                to="/my-applications" 
                className="flex items-center gap-3 px-4 py-3 hover:bg-stone-50"
                onClick={() => setMobileMenuOpen(false)}
              >
                <FileText className="w-5 h-5 text-[#57534E]" />
                <span>My Applications</span>
              </Link>
              {!isPremium && (
                <Link 
                  to="/upgrade" 
                  className="flex items-center gap-3 px-4 py-3 hover:bg-stone-50 text-[#E76F51]"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <Crown className="w-5 h-5" />
                  <span>Upgrade to Premium</span>
                </Link>
              )}
              <Link 
                to="/settings" 
                className="flex items-center gap-3 px-4 py-3 hover:bg-stone-50"
                onClick={() => setMobileMenuOpen(false)}
              >
                <Settings className="w-5 h-5 text-[#57534E]" />
                <span>Settings</span>
              </Link>
              <button 
                onClick={() => { handleLogout(); setMobileMenuOpen(false); }}
                className="flex items-center gap-3 px-4 py-3 hover:bg-stone-50 text-red-600 w-full"
              >
                <LogOut className="w-5 h-5" />
                <span>Log out</span>
              </button>
            </nav>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="container-app py-6">
        <Outlet />
      </main>

      {/* Mobile Bottom Navigation */}
      {isAuthenticated && (
        <nav className="mobile-nav md:hidden">
          <div className="flex items-center justify-around">
            <Link 
              to="/" 
              className={`flex flex-col items-center gap-1 py-1 px-3 ${isActive('/') ? 'text-[#E76F51]' : 'text-[#57534E]'}`}
              data-testid="mobile-nav-home"
            >
              <Home className="w-5 h-5" />
              <span className="text-xs">Home</span>
            </Link>
            <Link 
              to="/my-dates" 
              className={`flex flex-col items-center gap-1 py-1 px-3 ${isActive('/my-dates') ? 'text-[#E76F51]' : 'text-[#57534E]'}`}
              data-testid="mobile-nav-dates"
            >
              <Calendar className="w-5 h-5" />
              <span className="text-xs">Dates</span>
            </Link>
            <Link 
              to="/dates/new" 
              className="flex flex-col items-center gap-1 py-1 px-3"
              data-testid="mobile-nav-create"
            >
              <div className="w-12 h-12 -mt-6 rounded-full bg-[#E76F51] flex items-center justify-center shadow-lg">
                <PlusCircle className="w-6 h-6 text-white" />
              </div>
            </Link>
            <Link 
              to="/chat" 
              className={`flex flex-col items-center gap-1 py-1 px-3 ${isActive('/chat') ? 'text-[#E76F51]' : 'text-[#57534E]'}`}
              data-testid="mobile-nav-chat"
            >
              <MessageCircle className="w-5 h-5" />
              <span className="text-xs">Chat</span>
            </Link>
            <Link 
              to="/profile" 
              className={`flex flex-col items-center gap-1 py-1 px-3 ${isActive('/profile') ? 'text-[#E76F51]' : 'text-[#57534E]'}`}
              data-testid="mobile-nav-profile"
            >
              <User className="w-5 h-5" />
              <span className="text-xs">Profile</span>
            </Link>
          </div>
        </nav>
      )}
    </div>
  );
};

export default Layout;
