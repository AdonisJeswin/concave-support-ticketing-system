import React, { useContext, useEffect, useState } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const MemberDashboard = () => {
  const { api, user } = useContext(AuthContext);
  const [tickets, setTickets] = useState([]);
  const [categories, setCategories] = useState([]);
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const navigate = useNavigate();

  const fetchTickets = async () => {
    try {
      setIsLoading(true);
      const res = await api.get('/tickets');
      setTickets(res.data);
    } catch (err) {
      console.error('Failed to load member tickets:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const res = await api.get('/categories');
      setCategories(res.data);
      if (res.data.length && !categoryId) {
        setCategoryId(res.data[0].id);
      }
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  useEffect(() => {
    fetchTickets();
    fetchCategories();
  }, [api]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (subject.trim().length < 5 || subject.trim().length > 150) {
      alert('Subject must be between 5 and 150 characters long.');
      return;
    }
    if (description.trim().length < 10 || description.trim().length > 3000) {
      alert('Description must be between 10 and 3000 characters long.');
      return;
    }

    setIsSubmitting(true);
    setStatusMsg('');
    try {
      await api.post('/tickets', {
        subject: subject.trim(),
        description: description.trim(),
        category_id: Number(categoryId),
      });
      setSubject('');
      setDescription('');
      setStatusMsg('Ticket raised successfully!');
      fetchTickets();
    } catch (err) {
      alert('Failed to raise ticket: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsSubmitting(false);
    }
  };

  const selectedCategory = categories.find((c) => String(c.id) === String(categoryId));

  const getPriorityBadge = (priority) => {
    switch (priority) {
      case 'HIGH':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'MEDIUM':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'LOW':
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'OPEN':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'IN_PROGRESS':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'ESCALATED':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'RESOLVED':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'CLOSED':
        return 'bg-gray-100 text-gray-700 border-gray-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-6 border-b border-gray-200">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Member Portal</h1>
          <p className="text-sm text-gray-500 mt-1">
            Welcome, <span className="font-semibold text-gray-700">{user?.name}</span>. Raise support requests and track real-time resolution SLAs.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Ticket List (Left 2 cols) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-900">Your Support Tickets</h2>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100">
              {tickets.length} {tickets.length === 1 ? 'ticket' : 'tickets'}
            </span>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            {isLoading ? (
              <div className="p-8 text-center text-sm text-gray-500">Loading your tickets...</div>
            ) : tickets.length === 0 ? (
              <div className="p-12 text-center">
                <div className="w-12 h-12 rounded-full bg-indigo-50 text-indigo-500 flex items-center justify-center mx-auto mb-3 font-semibold text-lg">
                  ✓
                </div>
                <h3 className="text-sm font-semibold text-gray-800">No active tickets</h3>
                <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
                  You have not raised any support requests yet. Use the form to submit a new inquiry.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
                  <thead className="bg-gray-50/75 text-gray-600 font-semibold text-xs uppercase tracking-wider">
                    <tr>
                      <th className="px-4 py-3">Ticket #</th>
                      <th className="px-4 py-3">Subject</th>
                      <th className="px-4 py-3">Category</th>
                      <th className="px-4 py-3">Priority</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">SLA Status</th>
                      <th className="px-4 py-3">Due By</th>
                      <th className="px-4 py-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 bg-white">
                    {tickets.map((t) => (
                      <tr key={t.id} className="hover:bg-gray-50/80 transition-colors">
                        <td className="px-4 py-3.5 font-mono text-xs font-semibold text-indigo-600">
                          {t.ticket_number}
                        </td>
                        <td className="px-4 py-3.5 font-medium text-gray-900 max-w-xs truncate">
                          {t.subject}
                        </td>
                        <td className="px-4 py-3.5 text-xs text-gray-600">
                          {t.category_name}
                        </td>
                        <td className="px-4 py-3.5">
                          <span className={`inline-flex px-2 py-0.5 text-[11px] font-semibold rounded-md border ${getPriorityBadge(t.priority)}`}>
                            {t.priority}
                          </span>
                        </td>
                        <td className="px-4 py-3.5">
                          <span className={`inline-flex px-2 py-0.5 text-[11px] font-semibold rounded-md border ${getStatusBadge(t.status)}`}>
                            {t.status}
                          </span>
                        </td>
                        <td className="px-4 py-3.5">
                          {t.is_paused ? (
                            <span className="inline-flex px-2 py-0.5 text-[11px] font-semibold rounded-md bg-amber-50 text-amber-700 border border-amber-200">
                              Waiting for Member
                            </span>
                          ) : t.is_overdue ? (
                            <span className="inline-flex px-2 py-0.5 text-[11px] font-semibold rounded-md bg-rose-50 text-rose-700 border border-rose-200">
                              Overdue
                            </span>
                          ) : (
                            <span className="inline-flex px-2 py-0.5 text-[11px] font-semibold rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200">
                              Active SLA
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3.5 text-xs text-gray-500 whitespace-nowrap">
                          {t.due_at ? new Date(t.due_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'}
                        </td>
                        <td className="px-4 py-3.5 text-right whitespace-nowrap">
                          <button
                            onClick={() => navigate(`/tickets/${t.id}`)}
                            className="inline-flex items-center text-xs font-semibold text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 px-2.5 py-1 rounded-md transition-colors"
                          >
                            View
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Raise New Ticket Form (Right 1 col) */}
        <div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sticky top-24">
            <h2 className="text-lg font-bold text-gray-900 mb-1">Raise a New Ticket</h2>
            <p className="text-xs text-gray-500 mb-5">
              Submit your issue and our support team will handle it under configured SLA rules.
            </p>

            {statusMsg && (
              <div className="mb-4 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-medium">
                {statusMsg}
              </div>
            )}

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Issue Category
                </label>
                <select
                  value={categoryId}
                  onChange={(e) => setCategoryId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
                {selectedCategory && (
                  <p className="text-[11px] text-gray-500 mt-1">
                    Auto-assigned default priority: <strong className="text-gray-700 font-semibold">{selectedCategory.default_priority}</strong>
                  </p>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Subject
                </label>
                <input
                  type="text"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder="Summary of the issue..."
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
                <p className="text-[11px] text-gray-400 mt-1">Minimum 5 characters</p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Description
                </label>
                <textarea
                  rows={4}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Provide detailed information regarding the problem..."
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
                <p className="text-[11px] text-gray-400 mt-1">Minimum 10 characters</p>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm shadow-sm hover:shadow focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-all disabled:opacity-50"
              >
                {isSubmitting ? 'Submitting Ticket...' : 'Submit Support Ticket'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MemberDashboard;
