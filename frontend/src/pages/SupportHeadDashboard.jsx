import React, { useContext, useEffect, useState } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const SupportHeadDashboard = () => {
  const { api } = useContext(AuthContext);
  const [metrics, setMetrics] = useState(null);
  const [escalated, setEscalated] = useState([]);
  const [tatSettings, setTatSettings] = useState([]);
  const [systemSettings, setSystemSettings] = useState(null);
  const [agents, setAgents] = useState([]);
  const [isChecking, setIsChecking] = useState(false);
  const navigate = useNavigate();

  const fetchAll = async () => {
    try {
      const [mRes, escRes, tatRes, sysRes, agRes] = await Promise.all([
        api.get('/admin/metrics'),
        api.get('/tickets?status=ESCALATED'),
        api.get('/admin/tat-settings'),
        api.get('/admin/system-settings'),
        api.get('/auth/agents'),
      ]);
      setMetrics(mRes.data);
      setEscalated(escRes.data);
      setTatSettings(tatRes.data);
      setSystemSettings(sysRes.data);
      setAgents(agRes.data);
    } catch (err) {
      console.error('Failed to load Support Head dashboard data:', err);
    }
  };

  useEffect(() => {
    fetchAll();
  }, [api]);

  const runEscalationCheck = async () => {
    setIsChecking(true);
    try {
      const res = await api.post('/admin/run-escalation-check');
      const count = res.data?.escalated_count ?? 0;
      alert(`Escalation check completed: ${count} ticket(s) evaluated/escalated.`);
      fetchAll();
    } catch (err) {
      alert('Escalation check failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsChecking(false);
    }
  };

  const reassignEscalated = async (ticketId, agentId) => {
    const reason = prompt('Directive reason for reassigning escalated ticket (minimum 5 characters):');
    if (!reason || reason.trim().length < 5) {
      alert('A directive reason with at least 5 characters is mandatory.');
      return;
    }
    try {
      await api.post(`/tickets/${ticketId}/reassign-escalated`, {
        new_agent_id: Number(agentId),
        directive_reason: reason.trim(),
      });
      alert('Escalated ticket reassigned successfully.');
      fetchAll();
    } catch (err) {
      alert('Failed to reassign escalated ticket: ' + (err.response?.data?.detail || err.message));
    }
  };

  const updateTat = async (priority, hours) => {
    try {
      await api.put(`/admin/tat-settings/${priority}`, { tat_hours: hours });
      alert(`TAT SLA for priority ${priority} updated to ${hours} hours.`);
      fetchAll();
    } catch (err) {
      alert('Failed to update TAT setting: ' + (err.response?.data?.detail || err.message));
    }
  };

  const updateSystem = async (field, value) => {
    try {
      await api.put('/admin/system-settings', { [field]: value });
      alert(`System setting "${field}" updated to ${value}.`);
      fetchAll();
    } catch (err) {
      alert('Failed to update system setting: ' + (err.response?.data?.detail || err.message));
    }
  };

  if (!metrics) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center text-gray-500">
        <div className="animate-pulse">Loading executive metrics and system settings...</div>
      </div>
    );
  }

  const categoryEntries = Object.entries(metrics.category_breakdown || {});
  const totalCategoryTickets = categoryEntries.reduce((sum, [, count]) => sum + count, 0);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-6 border-b border-gray-200">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Executive Dashboard &amp; Administration</h1>
          <p className="text-sm text-gray-500 mt-1">
            Real-time SLA monitoring, escalation handling, and operational configuration.
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <button
            onClick={runEscalationCheck}
            disabled={isChecking}
            className="inline-flex items-center px-4 py-2 border border-transparent text-xs font-bold rounded-lg text-white bg-rose-600 hover:bg-rose-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-rose-500 focus:ring-offset-2 transition-all disabled:opacity-50"
          >
            {isChecking ? 'Running Check...' : 'Trigger Escalation Check'}
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Total Open</span>
          <p className="text-3xl font-extrabold text-blue-600 mt-2">{metrics.total_open_tickets}</p>
          <span className="text-[11px] text-gray-400">Open &amp; active tickets</span>
        </div>

        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Overdue</span>
          <p className="text-3xl font-extrabold text-rose-600 mt-2">{metrics.overdue_tickets_count}</p>
          <span className="text-[11px] text-gray-400">Past SLA target</span>
        </div>

        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Escalated</span>
          <p className="text-3xl font-extrabold text-purple-600 mt-2">{metrics.escalated_tickets_count}</p>
          <span className="text-[11px] text-gray-400">Requires directive action</span>
        </div>

        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Resolved Today</span>
          <p className="text-3xl font-extrabold text-emerald-600 mt-2">{metrics.resolved_today_count}</p>
          <span className="text-[11px] text-gray-400">Closed/resolved since midnight</span>
        </div>

        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Avg Resolution</span>
          <p className="text-2xl font-extrabold text-indigo-600 mt-2">
            {metrics.average_resolution_time_hours != null
              ? `${metrics.average_resolution_time_hours} hrs`
              : 'N/A'}
          </p>
          <span className="text-[11px] text-gray-400">Lifetime average resolution</span>
        </div>
      </div>

      {/* Category Breakdown Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-gray-900">Category Volume Breakdown</h2>
          <span className="text-xs text-gray-500">{totalCategoryTickets} total categorized tickets</span>
        </div>

        {categoryEntries.length === 0 ? (
          <p className="text-sm text-gray-400">No category statistics available.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {categoryEntries.map(([catName, count]) => {
              const pct = totalCategoryTickets > 0 ? Math.round((count / totalCategoryTickets) * 100) : 0;
              return (
                <div key={catName} className="p-3.5 bg-gray-50 rounded-lg border border-gray-100">
                  <div className="flex justify-between items-center text-xs font-medium mb-1.5">
                    <span className="text-gray-800 font-semibold">{catName}</span>
                    <span className="text-gray-500">{count} tickets ({pct}%)</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Escalated Tickets Queue */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-gray-900">Escalated Tickets Queue</h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Overdue tickets automatically escalated by the SLA engine. Reassignment requires a directive audit reason.
            </p>
          </div>
          <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-purple-50 text-purple-700 border border-purple-200">
            {escalated.length} escalated
          </span>
        </div>

        {escalated.length === 0 ? (
          <div className="p-8 text-center text-sm text-gray-500">
            All tickets are currently within SLA compliance. No escalated tickets.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
              <thead className="bg-gray-50/75 text-gray-600 font-semibold text-xs uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Ticket #</th>
                  <th className="px-4 py-3">Subject</th>
                  <th className="px-4 py-3">Priority</th>
                  <th className="px-4 py-3">Directive Reassignment</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {escalated.map((t) => (
                  <tr key={t.id} className="hover:bg-purple-50/30 transition-colors">
                    <td className="px-4 py-3.5 font-mono text-xs font-semibold text-indigo-600">
                      {t.ticket_number}
                    </td>
                    <td className="px-4 py-3.5 font-medium text-gray-900 max-w-sm truncate">
                      {t.subject}
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="inline-flex px-2 py-0.5 text-[11px] font-bold rounded-md bg-purple-50 text-purple-700 border border-purple-200">
                        {t.priority}
                      </span>
                    </td>
                    <td className="px-4 py-3.5">
                      <select
                        onChange={(e) => {
                          if (e.target.value) {
                            reassignEscalated(t.id, e.target.value);
                            e.target.value = '';
                          }
                        }}
                        defaultValue=""
                        className="px-2.5 py-1 text-xs border border-purple-300 rounded-md bg-white text-gray-700 focus:outline-none focus:ring-1 focus:ring-purple-500"
                      >
                        <option value="" disabled>Select Target Agent (prompts reason)</option>
                        {agents.map((a) => (
                          <option key={a.id} value={a.id}>{a.name}</option>
                        ))}
                      </select>
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

      {/* Admin Settings: TAT and Global Policy */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* TAT SLA Settings */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-base font-bold text-gray-900 mb-1">Turnaround Time (TAT) SLA Matrix</h2>
          <p className="text-xs text-gray-500 mb-4">
            Configure resolution hour limits mapped to ticket priority levels.
          </p>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50/75 text-gray-600 font-semibold text-xs uppercase tracking-wider">
                <tr>
                  <th className="px-3 py-2 text-left">Priority</th>
                  <th className="px-3 py-2 text-center">SLA Limit (Hours)</th>
                  <th className="px-3 py-2 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {tatSettings.map((s) => (
                  <tr key={s.priority}>
                    <td className="px-3 py-3 font-semibold text-gray-800 text-xs">
                      {s.priority}
                    </td>
                    <td className="px-3 py-3 text-center">
                      <input
                        type="number"
                        defaultValue={s.tat_hours}
                        min="1"
                        max="168"
                        className="w-20 px-2 py-1 text-xs text-center border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        id={`tat-${s.priority}`}
                      />
                    </td>
                    <td className="px-3 py-3 text-right">
                      <button
                        onClick={() => {
                          const val = parseInt(document.getElementById(`tat-${s.priority}`).value, 10);
                          if (val > 0) updateTat(s.priority, val);
                        }}
                        className="inline-flex text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 px-3 py-1 rounded-md transition-colors"
                      >
                        Save
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Global Policy Settings */}
        {systemSettings && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
            <div>
              <h2 className="text-base font-bold text-gray-900 mb-1">Global System Policies</h2>
              <p className="text-xs text-gray-500">
                Configure ticket lifecycle rules: reopen windows, maximum attempts, and auto-closure.
              </p>
            </div>

            <div className="space-y-4 pt-2">
              <div className="p-3 bg-gray-50 rounded-lg border border-gray-100 flex items-center justify-between">
                <div>
                  <label className="block text-xs font-semibold text-gray-800">
                    Reopen Window
                  </label>
                  <span className="text-[11px] text-gray-500">Days allowed to reopen resolved ticket</span>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="number"
                    defaultValue={systemSettings.reopen_window_days}
                    min="1"
                    max="90"
                    className="w-16 px-2 py-1 text-xs text-center border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    id="reopen_window"
                  />
                  <button
                    onClick={() => {
                      const val = parseInt(document.getElementById('reopen_window').value, 10);
                      if (val > 0) updateSystem('reopen_window_days', val);
                    }}
                    className="text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 px-2.5 py-1 rounded-md transition-colors"
                  >
                    Save
                  </button>
                </div>
              </div>

              <div className="p-3 bg-gray-50 rounded-lg border border-gray-100 flex items-center justify-between">
                <div>
                  <label className="block text-xs font-semibold text-gray-800">
                    Max Reopen Attempts
                  </label>
                  <span className="text-[11px] text-gray-500">Maximum times a member can reopen</span>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="number"
                    defaultValue={systemSettings.max_reopen_attempts}
                    min="0"
                    max="10"
                    className="w-16 px-2 py-1 text-xs text-center border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    id="max_reopen"
                  />
                  <button
                    onClick={() => {
                      const val = parseInt(document.getElementById('max_reopen').value, 10);
                      if (val >= 0) updateSystem('max_reopen_attempts', val);
                    }}
                    className="text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 px-2.5 py-1 rounded-md transition-colors"
                  >
                    Save
                  </button>
                </div>
              </div>

              <div className="p-3 bg-gray-50 rounded-lg border border-gray-100 flex items-center justify-between">
                <div>
                  <label className="block text-xs font-semibold text-gray-800">
                    Auto-Close Days
                  </label>
                  <span className="text-[11px] text-gray-500">Days resolved ticket remains before auto-closing</span>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="number"
                    defaultValue={systemSettings.auto_close_days ?? 3}
                    min="1"
                    max="90"
                    className="w-16 px-2 py-1 text-xs text-center border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    id="auto_close"
                  />
                  <button
                    onClick={() => {
                      const val = parseInt(document.getElementById('auto_close').value, 10);
                      if (val > 0) updateSystem('auto_close_days', val);
                    }}
                    className="text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 px-2.5 py-1 rounded-md transition-colors"
                  >
                    Save
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SupportHeadDashboard;
