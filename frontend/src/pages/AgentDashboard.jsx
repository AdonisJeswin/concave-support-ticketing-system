import React, { useContext, useEffect, useState } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const AgentDashboard = () => {
  const { api, user } = useContext(AuthContext);
  const [tickets, setTickets] = useState([]);
  const [agents, setAgents] = useState([]);
  const [categories, setCategories] = useState([]);
  const [filters, setFilters] = useState({ status: '', priority: '', category_id: '', is_overdue: false, search: '' });
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const fetchTickets = async () => {
    try {
      setIsLoading(true);
      const params = {};
      if (filters.status) params.status = filters.status;
      if (filters.priority) params.priority = filters.priority;
      if (filters.category_id) params.category_id = filters.category_id;
      if (filters.is_overdue) params.is_overdue = true;
      if (filters.search) params.search = filters.search;

      const res = await api.get('/tickets', { params });
      setTickets(res.data);
    } catch (err) {
      console.error('Failed to load tickets queue:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAgents = async () => {
    try {
      const res = await api.get('/auth/agents');
      setAgents(res.data);
    } catch (err) {
      console.error('Failed to fetch agents list:', err);
    }
  };

  const fetchCategories = async () => {
    try {
      const res = await api.get('/categories');
      setCategories(res.data);
    } catch (err) {
      console.error('Failed to fetch categories:', err);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, [api, filters]);

  useEffect(() => {
    fetchAgents();
    fetchCategories();
  }, [api]);

  const claimTicket = async (id) => {
    try {
      await api.patch(`/tickets/${id}/assign`, { assigned_agent_id: user.id });
      fetchTickets();
    } catch (err) {
      alert('Failed to claim ticket: ' + (err.response?.data?.detail || err.message));
    }
  };

  const reassignTicket = async (id, agentId) => {
    try {
      await api.patch(`/tickets/${id}/assign`, { assigned_agent_id: Number(agentId) });
      fetchTickets();
    } catch (err) {
      alert('Failed to reassign ticket: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleFilterChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFilters((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const formatSlaCountdown = (seconds) => {
    if (seconds == null) return '—';
    if (seconds <= 0) return '0h 0m (Overdue)';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

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
        return 'bg-purple-50 text-purple-700 border-purple-200 font-bold';
      case 'RESOLVED':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'CLOSED':
        return 'bg-gray-100 text-gray-700 border-gray-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-6 border-b border-gray-200">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Support Agent Queue</h1>
          <p className="text-sm text-gray-500 mt-1">
            Manage incoming inquiries, claim tickets, and uphold SLAs.
          </p>
        </div>
        <div className="mt-4 sm:mt-0 flex items-center space-x-2">
          <span className="text-xs font-medium text-gray-500">Queue size:</span>
          <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100">
            {tickets.length} tickets
          </span>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          <div>
            <label className="block text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
              Status
            </label>
            <select
              name="status"
              value={filters.status}
              onChange={handleFilterChange}
              className="w-full px-2.5 py-1.5 border border-gray-300 rounded-lg text-xs bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">All Statuses</option>
              <option value="OPEN">OPEN</option>
              <option value="IN_PROGRESS">IN_PROGRESS</option>
              <option value="ESCALATED">ESCALATED</option>
              <option value="RESOLVED">RESOLVED</option>
              <option value="CLOSED">CLOSED</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
              Priority
            </label>
            <select
              name="priority"
              value={filters.priority}
              onChange={handleFilterChange}
              className="w-full px-2.5 py-1.5 border border-gray-300 rounded-lg text-xs bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">All Priorities</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
              Category
            </label>
            <select
              name="category_id"
              value={filters.category_id}
              onChange={handleFilterChange}
              className="w-full px-2.5 py-1.5 border border-gray-300 rounded-lg text-xs bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">All Categories</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
              Search
            </label>
            <input
              name="search"
              type="text"
              placeholder="Search subject / number..."
              value={filters.search}
              onChange={handleFilterChange}
              className="w-full px-2.5 py-1.5 border border-gray-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="flex items-end pb-1.5">
            <label className="inline-flex items-center text-xs font-semibold text-gray-700 cursor-pointer select-none">
              <input
                type="checkbox"
                name="is_overdue"
                checked={filters.is_overdue}
                onChange={handleFilterChange}
                className="w-4 h-4 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500 mr-2"
              />
              Overdue Tickets Only
            </label>
          </div>
        </div>
      </div>

      {/* Tickets Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-sm text-gray-500">Loading support queue...</div>
        ) : tickets.length === 0 ? (
          <div className="p-12 text-center">
            <p className="text-sm font-semibold text-gray-700">No tickets match current filters</p>
            <p className="text-xs text-gray-400 mt-1">Try resetting the status or priority filters.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
              <thead className="bg-gray-50/75 text-gray-600 font-semibold text-xs uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Ticket #</th>
                  <th className="px-4 py-3">Subject</th>
                  <th className="px-4 py-3">Priority</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Assigned Agent</th>
                  <th className="px-4 py-3">SLA Status</th>
                  <th className="px-4 py-3">Remaining SLA</th>
                  <th className="px-4 py-3 text-right">Actions</th>
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
                    <td className="px-4 py-3.5 text-xs text-gray-700">
                      {t.assigned_agent_name ? (
                        <span className="font-medium text-gray-900">{t.assigned_agent_name}</span>
                      ) : (
                        <span className="text-gray-400 italic">Unassigned</span>
                      )}
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      {t.is_paused ? (
                        <span className="inline-flex px-2 py-0.5 text-[11px] font-semibold rounded-md bg-amber-50 text-amber-700 border border-amber-200">
                          Paused (Waiting Member)
                        </span>
                      ) : t.is_overdue ? (
                        <span className="inline-flex px-2 py-0.5 text-[11px] font-semibold rounded-md bg-rose-50 text-rose-700 border border-rose-200">
                          Overdue
                        </span>
                      ) : (
                        <span className="inline-flex px-2 py-0.5 text-[11px] font-semibold rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200">
                          On Track
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3.5 text-xs font-mono whitespace-nowrap text-gray-600">
                      {formatSlaCountdown(t.remaining_sla_seconds)}
                    </td>
                    <td className="px-4 py-3.5 text-right whitespace-nowrap space-x-2">
                      {t.assigned_agent_id ? (
                        <select
                          onChange={(e) => {
                            if (e.target.value) {
                              reassignTicket(t.id, e.target.value);
                              e.target.value = '';
                            }
                          }}
                          defaultValue=""
                          disabled={t.status === 'ESCALATED'}
                          className="px-2 py-1 text-xs border border-gray-300 rounded-md bg-white text-gray-700 disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        >
                          <option value="" disabled>
                            {t.status === 'ESCALATED' ? 'Locked (Escalated)' : 'Reassign Agent'}
                          </option>
                          {agents.map((a) => (
                            <option key={a.id} value={a.id}>
                              {a.name}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <button
                          onClick={() => claimTicket(t.id)}
                          className="inline-flex items-center text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 px-2.5 py-1 rounded-md shadow-sm transition-colors"
                        >
                          Claim
                        </button>
                      )}

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
  );
};

export default AgentDashboard;
