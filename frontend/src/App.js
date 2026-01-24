import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider, useAuth } from './context/AuthContext';
import AuthPage from './pages/AuthPage';
import OnboardingPage from './pages/OnboardingPage';
import MainApp from './pages/MainApp';
import './App.css';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, profileComplete, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FDFCF8]">
        <div className="animate-pulse text-[#E76F51] font-semibold text-lg">Loading...</div>
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }
  
  if (!profileComplete) {
    return <Navigate to="/onboarding" replace />;
  }
  
  return children;
};

const OnboardingRoute = ({ children }) => {
  const { isAuthenticated, profileComplete, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FDFCF8]">
        <div className="animate-pulse text-[#E76F51] font-semibold text-lg">Loading...</div>
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }
  
  if (profileComplete) {
    return <Navigate to="/" replace />;
  }
  
  return children;
};

const PublicRoute = ({ children }) => {
  const { isAuthenticated, profileComplete, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FDFCF8]">
        <div className="animate-pulse text-[#E76F51] font-semibold text-lg">Loading...</div>
      </div>
    );
  }
  
  if (isAuthenticated) {
    if (!profileComplete) {
      return <Navigate to="/onboarding" replace />;
    }
    return <Navigate to="/" replace />;
  }
  
  return children;
};

function AppRoutes() {
  return (
    <Routes>
      <Route path="/auth" element={
        <PublicRoute>
          <AuthPage />
        </PublicRoute>
      } />
      
      <Route path="/onboarding" element={
        <OnboardingRoute>
          <OnboardingPage />
        </OnboardingRoute>
      } />
      
      <Route path="/*" element={
        <ProtectedRoute>
          <MainApp />
        </ProtectedRoute>
      } />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="min-h-screen bg-[#FDFCF8]">
          <AppRoutes />
          <Toaster 
            position="top-center" 
            richColors 
            toastOptions={{
              style: { fontFamily: 'Manrope, sans-serif' },
            }}
          />
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
