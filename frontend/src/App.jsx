import React, { useContext } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthContext } from './context/AuthContext';
import Login from './pages/Login';
import MemberDashboard from './pages/MemberDashboard';
import AgentDashboard from './pages/AgentDashboard';
import SupportHeadDashboard from './pages/SupportHeadDashboard';
import TicketDetails from './pages/TicketDetails';
import Navbar from './components/Navbar';

const App = () => {
  const { user, loading } = useContext(AuthContext);

  const RequireAuth = ({ children, allowedRoles }) => {
    if (loading) {
      return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-500 text-sm">
          <div className="flex items-center space-x-2">
            <div className="w-2.5 h-2.5 bg-indigo-600 rounded-full animate-bounce" />
            <span>Loading authentication...</span>
          </div>
        </div>
      );
    }

    if (!user) return <Navigate to="/login" replace />;

    if (allowedRoles && !allowedRoles.includes(user.role)) {
      switch (user.role) {
        case 'MEMBER':
          return <Navigate to="/dashboard" replace />;
        case 'AGENT':
          return <Navigate to="/agent/queue" replace />;
        case 'SUPPORT_HEAD':
          return <Navigate to="/admin/dashboard" replace />;
        default:
          return <Navigate to="/login" replace />;
      }
    }

    return (
      <>
        <Navbar />
        {children}
      </>
    );
  };

  const RoleRedirect = () => {
    if (loading) {
      return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-500 text-sm">
          <div className="flex items-center space-x-2">
            <div className="w-2.5 h-2.5 bg-indigo-600 rounded-full animate-bounce" />
            <span>Loading authentication...</span>
          </div>
        </div>
      );
    }

    if (!user) return <Navigate to="/login" replace />;

    switch (user.role) {
      case 'MEMBER':
        return <Navigate to="/dashboard" replace />;
      case 'AGENT':
        return <Navigate to="/agent/queue" replace />;
      case 'SUPPORT_HEAD':
        return <Navigate to="/admin/dashboard" replace />;
      default:
        return <Navigate to="/login" replace />;
    }
  };

  return (
    <Routes>
      <Route path="/" element={<RoleRedirect />} />
      <Route path="/login" element={<Login />} />
      <Route
        path="/dashboard"
        element={
          <RequireAuth allowedRoles={['MEMBER']}>
            <MemberDashboard />
          </RequireAuth>
        }
      />
      <Route
        path="/agent/queue"
        element={
          <RequireAuth allowedRoles={['AGENT', 'SUPPORT_HEAD']}>
            <AgentDashboard />
          </RequireAuth>
        }
      />
      <Route
        path="/admin/dashboard"
        element={
          <RequireAuth allowedRoles={['SUPPORT_HEAD']}>
            <SupportHeadDashboard />
          </RequireAuth>
        }
      />
      <Route
        path="/tickets/:id"
        element={
          <RequireAuth allowedRoles={['MEMBER', 'AGENT', 'SUPPORT_HEAD']}>
            <TicketDetails />
          </RequireAuth>
        }
      />
    </Routes>
  );
};

export default App;
