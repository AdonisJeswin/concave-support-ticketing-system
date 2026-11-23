import React, { useContext, useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

const TicketDetails = () => {
  const { id } = useParams();
  const { api, user } = useContext(AuthContext);
  const [ticket, setTicket] = useState(null);
  const [replies, setReplies] = useState([]);
  const [history, setHistory] = useState([]);
  const [message, setMessage] = useState('');
  const [pause, setPause] = useState(false);
  const [newPriority, setNewPriority] = useState('');
  const [priorityReason, setPriorityReason] = useState('');
  const [agents, setAgents] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState(null);
  const [isSubmittingReply, setIsSubmittingReply] = useState(false);
  const navigate = useNavigate();

  const loadTicket = async () => {
    try {
      setIsLoading(true);
      setErrorMsg(null);
      const res = await api.get(`/tickets/${id}`);
      setTicket(res.data);
      setReplies(res.data.replies || []);
      setHistory(res.data.history || []);
      setNewPriority(res.data.priority);
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Failed to load ticket details.');
    } finally {
      setIsLoading(false);
    }
  };

  const loadAgents = async () => {
    try {
      const res = await api.get('/auth/agents');
      setAgents(res.data);
    } catch {
      // Non-staff roles cannot list agents
    }
  };

  useEffect(() => {
    loadTicket();
    loadAgents();
  }, [api, id]);

  const isMember = user?.role === 'MEMBER';
  const isAgent = user?.role === 'AGENT';
  const isHead = user?.role === 'SUPPORT_HEAD';

  const backLink = () => {
    if (isHead) return '/admin/dashboard';
    if (isAgent) return '/agent/queue';
    return '/dashboard';
  };

  const submitReply = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;

    setIsSubmittingReply(true);
    try {
      const payload = { message: message.trim() };
      if (!isMember) {
        payload.is_waiting_for_member = pause;
      }
      await api.post(`/tickets/${id}/replies`, payload);
      setMessage('');
      setPause(false);
      loadTicket();
    } catch (err) {
      alert('Failed to send reply: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsSubmittingReply(false);
    }
  };

  const changePriority = async (e) => {
    e.preventDefault();
    if (!priorityReason.trim()) {
      alert('A reason is mandatory when updating ticket priority.');
      return;
    }
    try {
      await api.patch(`/tickets/${id}/priority`, {
        priority: newPriority,
        reason: priorityReason.trim(),
      });
      setPriorityReason('');
      alert(`Priority updated to ${newPriority}`);
      loadTicket();
    } catch (err) {
      alert('Failed to change priority: ' + (err.response?.data?.detail || err.message));
    }
  };

  const resolveTicket = async () => {
    const note = prompt('Optional resolution note explaining the fix:');
    try {
      await api.post(`/tickets/${id}/resolve`, { resolution_note: note ? note.trim() : null });
      alert('Ticket marked as resolved.');
      loadTicket();
    } catch (err) {
      alert('Failed to resolve ticket: ' + (err.response?.data?.detail || err.message));
    }
  };

  const closeTicket = async () => {
    if (!window.confirm('Are you satisfied with the resolution and wish to close this ticket permanently?')) return;
    try {
      await api.post(`/tickets/${id}/close`);
      alert('Ticket closed. Thank you!');
      navigate('/dashboard');
    } catch (err) {
      alert('Failed to close ticket: ' + (err.response?.data?.detail || err.message));
    }
  };

  const reopenTicket = async () => {
    const reason = prompt('Reason for reopening this ticket (minimum 10 characters required):');
    if (!reason || reason.trim().length < 10) {
      alert('A descriptive reason of at least 10 characters is required to reopen a ticket.');
      return;
    }
    try {
      await api.post(`/tickets/${id}/reopen`, { reason: reason.trim() });
      alert('Ticket has been reopened.');
      loadTicket();
    } catch (err) {
      alert('Failed to reopen ticket: ' + (err.response?.data?.detail || err.message));
    }
  };

  const reassignEscalated = async (agentId) => {
    const reason = prompt('Directive reason for reassigning this escalated ticket (min 5 characters):');
    if (!reason || reason.trim().length < 5) {
      alert('Directive reason must be at least 5 characters.');
      return;
    }
    try {
      await api.post(`/tickets/${id}/reassign-escalated`, {
        new_agent_id: Number(agentId),
        directive_reason: reason.trim(),
      });
      alert('Escalated ticket reassigned.');
      loadTicket();
    } catch (err) {
      alert('Failed to reassign escalated ticket: ' + (err.response?.data?.detail || err.message));
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-16 text-center text-gray-500">
        <div className="animate-pulse flex items-center justify-center space-x-2">
          <div className="w-2 h-2 bg-indigo-600 rounded-full animate-ping" />
          <span className="text-sm font-medium">Loading ticket details...</span>
        </div>
      </div>
    );
  }

  if (errorMsg) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center">
        <div className="bg-rose-50 border border-rose-200 rounded-2xl p-8 max-w-lg mx-auto shadow-sm">
          <div className="w-12 h-12 bg-rose-100 text-rose-600 rounded-full flex items-center justify-center mx-auto mb-3 text-xl font-bold">
            !
          </div>
          <h2 className="text-base font-bold text-rose-800">Unable to Display Ticket</h2>
          <p className="text-xs text-rose-600 mt-2">{errorMsg}</p>
          <button
            onClick={() => navigate(backLink())}
            className="mt-6 inline-flex items-center px-4 py-2 text-xs font-semibold text-white bg-slate-800 hover:bg-slate-900 rounded-lg shadow-sm transition-colors"
          >
            &larr; Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!ticket) return null;

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
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Back Breadcrumb */}
      <div>
        <button
          onClick={() => navigate(backLink())}
          className="inline-flex items-center text-xs font-semibold text-gray-500 hover:text-indigo-600 transition-colors"
        >
          &larr; Back to {isHead ? 'Admin Dashboard' : isAgent ? 'Agent Queue' : 'My Tickets'}
        </button>
      </div>

      {/* Ticket Header Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-gray-100">
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-mono text-sm font-bold text-indigo-600">{ticket.ticket_number}</span>
              <span className={`inline-flex px-2 py-0.5 text-xs font-semibold rounded-md border ${getStatusBadge(ticket.status)}`}>
                {ticket.status}
              </span>
              <span className={`inline-flex px-2 py-0.5 text-xs font-semibold rounded-md border ${getPriorityBadge(ticket.priority)}`}>
                {ticket.priority} Priority
              </span>
            </div>
            <h1 className="text-xl font-bold text-gray-900 mt-2">{ticket.subject}</h1>
          </div>

          {/* Quick Action Toolbar */}
          <div className="flex items-center space-x-2">
            {(isAgent || isHead) && ticket.status !== 'RESOLVED' && ticket.status !== 'CLOSED' && (
              <button
                onClick={resolveTicket}
                className="inline-flex items-center px-3.5 py-1.5 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-sm transition-colors"
              >
                Mark Resolved
              </button>
            )}

            {isMember && ticket.status === 'RESOLVED' && (
              <div className="flex items-center space-x-2">
                <button
                  onClick={closeTicket}
                  className="inline-flex items-center px-3.5 py-1.5 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-sm transition-colors"
                >
                  Confirm &amp; Close
                </button>
                <button
                  onClick={reopenTicket}
                  className="inline-flex items-center px-3.5 py-1.5 text-xs font-semibold text-amber-700 bg-amber-50 hover:bg-amber-100 border border-amber-200 rounded-lg shadow-sm transition-colors"
                >
                  Reopen
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Metadata Details Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs pt-1">
          <div>
            <span className="text-gray-400 block font-semibold uppercase tracking-wider text-[10px]">Category</span>
            <span className="text-gray-800 font-medium mt-0.5 block">{ticket.category_name}</span>
          </div>
          <div>
            <span className="text-gray-400 block font-semibold uppercase tracking-wider text-[10px]">Assigned Agent</span>
            <span className="text-gray-800 font-medium mt-0.5 block">{ticket.assigned_agent_name || 'Unassigned'}</span>
          </div>
          <div>
            <span className="text-gray-400 block font-semibold uppercase tracking-wider text-[10px]">Created At</span>
            <span className="text-gray-800 font-medium mt-0.5 block">{new Date(ticket.created_at).toLocaleString()}</span>
          </div>
          <div>
            <span className="text-gray-400 block font-semibold uppercase tracking-wider text-[10px]">SLA Target Due</span>
            <span className="text-gray-800 font-medium mt-0.5 block">{new Date(ticket.due_at).toLocaleString()}</span>
          </div>
        </div>

        {/* SLA Status Badges */}
        <div className="flex items-center gap-2 pt-2 border-t border-gray-100">
          {ticket.is_paused ? (
            <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
              ⏸ SLA Paused — Waiting for Member response
            </span>
          ) : ticket.is_overdue ? (
            <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
              ⚠️ SLA Overdue
            </span>
          ) : (
            <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              ✓ SLA Active
            </span>
          )}
        </div>

        {/* Initial Description */}
        <div className="pt-2">
          <span className="text-xs font-bold text-gray-700 block mb-1">Description:</span>
          <p className="text-sm text-gray-700 bg-gray-50 p-4 rounded-lg border border-gray-100 whitespace-pre-line leading-relaxed">
            {ticket.description}
          </p>
        </div>
      </div>

      {/* Support Head: Reassign Escalated Panel */}
      {isHead && ticket.status === 'ESCALATED' && (
        <div className="bg-purple-50/80 rounded-xl border border-purple-200 p-5 space-y-3">
          <div className="flex items-center space-x-2">
            <span className="text-base font-bold text-purple-900">Support Head Directive Reassignment</span>
          </div>
          <p className="text-xs text-purple-700">
            This ticket is in escalated status. You can reassign it directly with a mandatory audit directive reason.
          </p>
          <div className="flex items-center space-x-3 pt-1">
            <select
              id="escalated-target-agent"
              defaultValue=""
              className="text-xs px-3 py-2 border border-purple-300 rounded-lg bg-white text-gray-800 focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="" disabled>Select Target Agent</option>
              {agents.map((a) => (
                <option key={a.id} value={a.id}>{a.name}</option>
              ))}
            </select>
            <button
              onClick={() => {
                const sel = document.getElementById('escalated-target-agent');
                if (sel.value) reassignEscalated(sel.value);
              }}
              className="text-xs font-semibold text-white bg-purple-700 hover:bg-purple-800 px-4 py-2 rounded-lg transition-colors shadow-sm"
            >
              Reassign with Reason
            </button>
          </div>
        </div>
      )}

      {/* Priority Update Panel (Agents & Head) */}
      {(isAgent || isHead) && ticket.status !== 'CLOSED' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
          <h2 className="text-sm font-bold text-gray-900 mb-1">Adjust Priority &amp; SLA Level</h2>
          <p className="text-xs text-gray-500 mb-3">
            Changes will recalculate SLA target deadline and record a mandatory audit entry.
          </p>
          <form onSubmit={changePriority} className="flex flex-col sm:flex-row gap-3">
            <select
              value={newPriority}
              onChange={(e) => setNewPriority(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-xs bg-white text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="LOW">LOW</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="HIGH">HIGH</option>
            </select>
            <input
              type="text"
              placeholder="Mandatory reason for priority change..."
              value={priorityReason}
              onChange={(e) => setPriorityReason(e.target.value)}
              required
              className="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              type="submit"
              className="px-4 py-1.5 text-xs font-semibold text-white bg-slate-800 hover:bg-slate-900 rounded-lg shadow-sm transition-colors whitespace-nowrap"
            >
              Update Priority
            </button>
          </form>
        </div>
      )}

      {/* Conversation Thread */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-gray-100">
          <h2 className="text-base font-bold text-gray-900">Conversation &amp; Replies</h2>
          <span className="text-xs text-gray-500">{replies.length} replies</span>
        </div>

        {replies.length === 0 ? (
          <p className="text-sm text-gray-400 py-4 text-center">No replies posted yet.</p>
        ) : (
          <div className="space-y-4">
            {replies.map((r) => {
              const isStaff = r.sender_role === 'AGENT' || r.sender_role === 'SUPPORT_HEAD';
              return (
                <div
                  key={r.id}
                  className={`p-4 rounded-xl border ${
                    isStaff
                      ? 'bg-indigo-50/50 border-indigo-100 ml-4'
                      : 'bg-gray-50/70 border-gray-200 mr-4'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold text-gray-900">{r.sender_name}</span>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-white border border-gray-200 text-gray-600">
                        {r.sender_role}
                      </span>
                    </div>
                    <span className="text-[11px] text-gray-400">
                      {new Date(r.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-800 whitespace-pre-line leading-relaxed">
                    {r.message}
                  </p>
                </div>
              );
            })}
          </div>
        )}

        {/* Member Resume Notice */}
        {isMember && ticket.is_paused && (
          <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-xs font-medium flex items-center">
            <span className="mr-2 text-sm">ℹ️</span>
            Ticket is currently paused waiting for your response. Submitting a reply will automatically resume the SLA timer.
          </div>
        )}

        {/* Post Reply Form */}
        {ticket.status !== 'CLOSED' && (
          <form onSubmit={submitReply} className="pt-4 border-t border-gray-100 space-y-3">
            <textarea
              rows={3}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Type your reply message..."
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />

            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              {(isAgent || isHead) ? (
                <label className="inline-flex items-center text-xs font-semibold text-gray-700 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={pause}
                    onChange={(e) => setPause(e.target.checked)}
                    className="w-4 h-4 text-amber-600 rounded border-gray-300 focus:ring-amber-500 mr-2"
                  />
                  Waiting for Member (Pause SLA Timer)
                </label>
              ) : <div />}

              <button
                type="submit"
                disabled={isSubmittingReply}
                className="inline-flex items-center px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition-colors disabled:opacity-50"
              >
                {isSubmittingReply ? 'Sending Reply...' : 'Post Reply'}
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Member View: Status Progression (Partial / Status Only) */}
      {isMember && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-3">
          <div className="flex items-center justify-between pb-3 border-b border-gray-100">
            <h2 className="text-base font-bold text-gray-900">Status Progression</h2>
            <span className="text-xs text-gray-500">Lifecycle milestones</span>
          </div>
          <div className="space-y-3">
            {history
              .filter((h) => ['CREATED', 'STATUS_CHANGE', 'RESOLVED', 'CLOSED', 'REOPENED'].includes(h.action))
              .map((h, idx) => (
                <div key={h.id || idx} className="flex items-center justify-between text-xs p-2.5 bg-gray-50 rounded-lg border border-gray-100">
                  <div className="flex items-center space-x-2">
                    <span className="w-2 h-2 rounded-full bg-indigo-600" />
                    <span className="font-semibold text-gray-800">{h.action.replace('_', ' ')}</span>
                    {h.new_value && (
                      <span className="text-gray-500 font-medium">({h.new_value})</span>
                    )}
                  </div>
                  <span className="text-gray-400 text-[11px]">{new Date(h.created_at).toLocaleString()}</span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Audit Trail Timeline (Staff / Support Head only - Full System Log) */}
      {!isMember && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-3">
          <div className="flex items-center justify-between pb-3 border-b border-gray-100">
            <h2 className="text-base font-bold text-gray-900">Audit Trail &amp; Lifecycle Events</h2>
            <span className="text-xs text-gray-500">{history.length} records</span>
          </div>

          {history.length === 0 ? (
            <p className="text-sm text-gray-400 py-2">No audit log records found.</p>
          ) : (
            <div className="flow-root">
              <ul className="-mb-8">
                {history.map((h, hIdx) => (
                  <li key={h.id || hIdx}>
                    <div className="relative pb-6">
                      {hIdx !== history.length - 1 ? (
                        <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200" aria-hidden="true" />
                      ) : null}
                      <div className="relative flex space-x-3 text-xs">
                        <div>
                          <span className="h-8 w-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center font-bold text-slate-700 text-[10px]">
                            {h.action ? h.action.charAt(0) : '•'}
                          </span>
                        </div>
                        <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                          <div>
                            <p className="text-gray-800 font-semibold">
                              {h.action}
                              <span className="font-normal text-gray-500"> by </span>
                              <span className="text-indigo-600 font-medium">{h.actor_name || 'SYSTEM'}</span>
                            </p>
                            {h.reason && (
                              <p className="text-gray-600 italic mt-0.5 bg-gray-50 px-2 py-1 rounded border border-gray-100">
                                Reason: "{h.reason}"
                              </p>
                            )}
                          </div>
                          <div className="text-right whitespace-nowrap text-gray-400 text-[11px]">
                            {new Date(h.created_at).toLocaleString()}
                          </div>
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TicketDetails;
