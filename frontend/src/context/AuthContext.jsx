import React, { createContext, useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('concave_token') || null);
  const [loading, setLoading] = useState(!!token);
  const navigate = useNavigate();

  const api = axios.create({
    baseURL: '/api',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  // Attach token to every request
  api.interceptors.request.use((config) => {
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  });

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    const t = res.data.access_token;
    localStorage.setItem('concave_token', t);
    setToken(t);
    const me = await api.get('/auth/me', {
      headers: { Authorization: `Bearer ${t}` }
    });
    setUser(me.data);
    if (me.data.role === 'MEMBER') navigate('/dashboard');
    else if (me.data.role === 'AGENT') navigate('/agent/queue');
    else if (me.data.role === 'SUPPORT_HEAD') navigate('/admin/dashboard');
    else navigate('/dashboard');
  };

  const mockLogin = async (role) => {
    const res = await api.post('/auth/mock-login', { role });
    const t = res.data.access_token;
    localStorage.setItem('concave_token', t);
    setToken(t);
    const me = await api.get('/auth/me', {
      headers: { Authorization: `Bearer ${t}` }
    });
    setUser(me.data);
    if (role === 'MEMBER') navigate('/dashboard');
    else if (role === 'AGENT') navigate('/agent/queue');
    else if (role === 'SUPPORT_HEAD') navigate('/admin/dashboard');
  };

  const logout = () => {
    localStorage.removeItem('concave_token');
    setToken(null);
    setUser(null);
    navigate('/login');
  };

  // load current user on token change
  useEffect(() => {
    const loadUser = async () => {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const me = await api.get('/auth/me');
        setUser(me.data);
      } catch (e) {
        logout();
      } finally {
        setLoading(false);
      }
    };
    loadUser();
  }, [token]);

  return (
    <AuthContext.Provider value={{ user, token, api, login, mockLogin, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
