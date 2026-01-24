import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import AuthPage from './pages/AuthPage';
import ProfilePage from './pages/ProfilePage';
import CreateDatePage from './pages/CreateDatePage';
import DateDetailsPage from './pages/DateDetailsPage';
import ManageApplicantsPage from './pages/ManageApplicantsPage';
import ChatListPage from './pages/ChatListPage';
import ChatPage from './pages/ChatPage';
import UpgradePage from './pages/UpgradePage';
import SettingsPage from './pages/SettingsPage';
import MyDatesPage from './pages/MyDatesPage';
import MyApplicationsPage from './pages/MyApplicationsPage';
import './App.css';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FDFCF8]">
        <div className="animate-pulse text-[#E76F51] font-semibold">Loading...</div>
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }
  
  return children;
};

const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FDFCF8]">
        <div className="animate-pulse text-[#E76F51] font-semibold">Loading...</div>
      </div>
    );
  }
  
  if (isAuthenticated) {
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
      
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="dates/new" element={
          <ProtectedRoute>
            <CreateDatePage />
          </ProtectedRoute>
        } />
        <Route path="dates/:id" element={<DateDetailsPage />} />
        <Route path="dates/:id/manage" element={
          <ProtectedRoute>
            <ManageApplicantsPage />
          </ProtectedRoute>
        } />
        <Route path="my-dates" element={
          <ProtectedRoute>
            <MyDatesPage />
          </ProtectedRoute>
        } />
        <Route path="my-applications" element={
          <ProtectedRoute>
            <MyApplicationsPage />
          </ProtectedRoute>
        } />
        <Route path="profile" element={
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        } />
        <Route path="chat" element={
          <ProtectedRoute>
            <ChatListPage />
          </ProtectedRoute>
        } />
        <Route path="chat/:threadId" element={
          <ProtectedRoute>
            <ChatPage />
          </ProtectedRoute>
        } />
        <Route path="upgrade" element={
          <ProtectedRoute>
            <UpgradePage />
          </ProtectedRoute>
        } />
        <Route path="settings" element={
          <ProtectedRoute>
            <SettingsPage />
          </ProtectedRoute>
        } />
      </Route>
      
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="min-h-screen bg-[#FDFCF8]">
          <div className="noise-overlay" />
          <AppRoutes />
          <Toaster 
            position="top-center" 
            richColors 
            toastOptions={{
              style: {
                fontFamily: 'Manrope, sans-serif',
              },
            }}
          />
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
