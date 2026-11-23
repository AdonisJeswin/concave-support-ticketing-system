import React, { useContext, useState } from 'react';
import { AuthContext } from '../context/AuthContext';

const Login = () => {
  const { login, mockLogin } = useContext(AuthContext);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setIsLoading(true);
    try {
      await login(email, password);
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Invalid email or password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async (role) => {
    setErrorMsg('');
    setIsLoading(true);
    try {
      await mockLogin(role);
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Demo login failed. Make sure the backend server is running.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-950 flex flex-col justify-center items-center px-4 py-12 sm:px-6 lg:px-8">
      {/* Brand Header */}
      <div className="text-center mb-8">
        <div className="inline-flex w-12 h-12 rounded-xl bg-gradient-to-tr from-indigo-500 to-cyan-400 items-center justify-center font-black text-white text-2xl shadow-lg mb-3">
          C
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          Concave Insights
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Support Ticketing &amp; SLA Management Platform
        </p>
      </div>

      <div className="max-w-md w-full space-y-6">
        {/* Main Login Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-slate-100">
          <h2 className="text-xl font-bold text-slate-800 mb-6 text-center">
            Sign in to your account
          </h2>

          {errorMsg && (
            <div className="mb-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
              {errorMsg}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                required
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm shadow-md hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-all disabled:opacity-50"
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        </div>

        {/* Demo Fast-Login Selector Card */}
        <div className="bg-slate-800/80 backdrop-blur-sm rounded-2xl p-6 border border-slate-700/60 shadow-lg text-center">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
            One-Click Evaluator Demo Access
          </p>
          <div className="grid grid-cols-3 gap-2.5">
            <button
              type="button"
              onClick={() => handleDemoLogin('MEMBER')}
              disabled={isLoading}
              className="flex flex-col items-center justify-center p-3 rounded-xl bg-slate-900/80 hover:bg-emerald-950/80 border border-slate-700 hover:border-emerald-500 text-emerald-400 hover:text-emerald-300 transition-all group"
            >
              <span className="font-bold text-xs">Member</span>
              <span className="text-[10px] text-slate-400 group-hover:text-emerald-300/80 mt-0.5">Customer Portal</span>
            </button>

            <button
              type="button"
              onClick={() => handleDemoLogin('AGENT')}
              disabled={isLoading}
              className="flex flex-col items-center justify-center p-3 rounded-xl bg-slate-900/80 hover:bg-blue-950/80 border border-slate-700 hover:border-blue-500 text-blue-400 hover:text-blue-300 transition-all group"
            >
              <span className="font-bold text-xs">Support Agent</span>
              <span className="text-[10px] text-slate-400 group-hover:text-blue-300/80 mt-0.5">Queue &amp; SLA</span>
            </button>

            <button
              type="button"
              onClick={() => handleDemoLogin('SUPPORT_HEAD')}
              disabled={isLoading}
              className="flex flex-col items-center justify-center p-3 rounded-xl bg-slate-900/80 hover:bg-purple-950/80 border border-slate-700 hover:border-purple-500 text-purple-400 hover:text-purple-300 transition-all group"
            >
              <span className="font-bold text-xs">Support Head</span>
              <span className="text-[10px] text-slate-400 group-hover:text-purple-300/80 mt-0.5">Admin &amp; Policy</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
