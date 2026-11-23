import React, { useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

const Navbar = () => {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const dashboardLink = () => {
    switch (user?.role) {
      case 'MEMBER':
        return '/dashboard';
      case 'AGENT':
        return '/agent/queue';
      case 'SUPPORT_HEAD':
        return '/admin/dashboard';
      default:
        return '/';
    }
  };

  const getRoleBadgeColor = (role) => {
    switch (role) {
      case 'SUPPORT_HEAD':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'AGENT':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'MEMBER':
      default:
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
    }
  };

  const getRoleLabel = (role) => {
    switch (role) {
      case 'SUPPORT_HEAD':
        return 'Support Head';
      case 'AGENT':
        return 'Support Agent';
      case 'MEMBER':
      default:
        return 'Member';
    }
  };

  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Product Name */}
          <div className="flex items-center space-x-3">
            <Link to={dashboardLink()} className="flex items-center space-x-2 group">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-cyan-400 flex items-center justify-center font-black text-white text-base shadow-sm group-hover:scale-105 transition-transform">
                C
              </div>
              <div className="flex flex-col">
                <span className="font-bold text-base tracking-tight text-white group-hover:text-cyan-300 transition-colors">
                  Concave Insights
                </span>
                <span className="text-xs text-slate-400 -mt-0.5">Support Desk</span>
              </div>
            </Link>

            <span className="text-slate-600 hidden md:inline">|</span>

            <nav className="hidden md:flex space-x-1">
              <Link
                to={dashboardLink()}
                className="px-3 py-1.5 text-xs font-medium rounded-md text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
              >
                Dashboard
              </Link>
            </nav>
          </div>

          {/* User Profile & Actions */}
          {user && (
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-full bg-slate-700 border border-slate-600 flex items-center justify-center text-xs font-semibold text-slate-200">
                  {user.name ? user.name.charAt(0).toUpperCase() : 'U'}
                </div>
                <div className="hidden sm:flex flex-col text-right">
                  <span className="text-xs font-semibold text-slate-200 leading-tight">{user.name}</span>
                  <span className="text-[11px] text-slate-400">{user.email}</span>
                </div>
                <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${getRoleBadgeColor(user.role)}`}>
                  {getRoleLabel(user.role)}
                </span>
              </div>

              <div className="h-5 w-px bg-slate-800" />

              <button
                onClick={logout}
                className="inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-lg text-slate-300 bg-slate-800 hover:bg-rose-600 hover:text-white transition-all shadow-sm border border-slate-700 hover:border-rose-500"
              >
                Logout / Switch Role
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Navbar;
