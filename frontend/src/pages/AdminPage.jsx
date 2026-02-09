import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import axios from 'axios';
import { 
  Shield, Users, AlertTriangle, CheckCircle, XCircle, Clock,
  Eye, Ban, UserX, MessageSquare, Camera, ArrowLeft,
  TrendingUp, Activity, Star, ThumbsUp, BarChart3
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { useAuth } from '../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AdminPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [verifications, setVerifications] = useState([]);
  const [reports, setReports] = useState([]);
  const [auditLog, setAuditLog] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState(null);
  const [actionDialog, setActionDialog] = useState({ open: false, type: null, item: null });
  const [notes, setNotes] = useState('');

  useEffect(() => {
    if (!user?.is_admin) {
      navigate('/');
      return;
    }
    fetchData();
  }, [user]);

  const fetchData = async () => {
    try {
      const [statsRes, verificationsRes, reportsRes, auditRes] = await Promise.all([
        axios.get(`${API}/admin/stats`),
        axios.get(`${API}/admin/verifications?status=PENDING`),
        axios.get(`${API}/admin/reports?status=pending`),
        axios.get(`${API}/admin/audit-log?limit=20`)
      ]);
      setStats(statsRes.data);
      setVerifications(verificationsRes.data.submissions || []);
      setReports(reportsRes.data.reports || []);
      setAuditLog(auditRes.data.actions || []);
    } catch (error) {
      console.error('Failed to fetch admin data:', error);
      toast.error('Failed to load admin data');
    } finally {
      setLoading(false);
    }
  };

  const handleVerification = async (submissionId, status) => {
    try {
      await axios.put(`${API}/admin/verifications/${submissionId}`, { status, notes });
      toast.success(`Verification ${status.toLowerCase()}`);
      setActionDialog({ open: false, type: null, item: null });
      setNotes('');
      fetchData();
    } catch (error) {
      toast.error('Failed to update verification');
    }
  };

  const handleReport = async (reportId, status) => {
    try {
      await axios.put(`${API}/admin/reports/${reportId}?status=${status}&notes=${encodeURIComponent(notes)}`);
      toast.success('Report updated');
      setActionDialog({ open: false, type: null, item: null });
      setNotes('');
      fetchData();
    } catch (error) {
      toast.error('Failed to update report');
    }
  };

  const handleUserAction = async (userId, action, reason) => {
    try {
      await axios.post(`${API}/admin/users/${userId}/action`, { action, reason });
      toast.success(`Action "${action}" taken`);
      setActionDialog({ open: false, type: null, item: null });
      setNotes('');
      fetchData();
    } catch (error) {
      toast.error('Failed to take action');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#FDFCF8] flex items-center justify-center">
        <div className="animate-pulse text-[#E76F51]">Loading admin panel...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FDFCF8] pb-24">
      {/* Header */}
      <div className="bg-white border-b border-stone-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center gap-3">
          <button onClick={() => navigate(-1)} className="p-2 hover:bg-stone-100 rounded-full">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <Shield className="w-6 h-6 text-[#E76F51]" />
            <h1 className="text-xl font-bold" style={{ fontFamily: 'Syne, sans-serif' }}>Admin Panel</h1>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-2xl font-bold text-[#1C1917]">{stats?.total_users || 0}</p>
                  <p className="text-sm text-[#57534E]">Total Users</p>
                </div>
                <Users className="w-8 h-8 text-[#2A9D8F]" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-2xl font-bold text-[#1C1917]">{stats?.pending_verifications || 0}</p>
                  <p className="text-sm text-[#57534E]">Pending Verifications</p>
                </div>
                <Camera className="w-8 h-8 text-[#E9C46A]" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-2xl font-bold text-[#1C1917]">{stats?.pending_reports || 0}</p>
                  <p className="text-sm text-[#57534E]">Pending Reports</p>
                </div>
                <AlertTriangle className="w-8 h-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-2xl font-bold text-[#1C1917]">{stats?.total_matches || 0}</p>
                  <p className="text-sm text-[#57534E]">Total Matches</p>
                </div>
                <TrendingUp className="w-8 h-8 text-[#E76F51]" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="verifications" className="w-full">
          <TabsList className="w-full mb-6">
            <TabsTrigger value="verifications" className="flex-1">
              Verifications ({verifications.length})
            </TabsTrigger>
            <TabsTrigger value="reports" className="flex-1">
              Reports ({reports.length})
            </TabsTrigger>
            <TabsTrigger value="audit" className="flex-1">
              Audit Log
            </TabsTrigger>
          </TabsList>

          {/* Verifications */}
          <TabsContent value="verifications">
            {verifications.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center text-[#A8A29E]">
                  No pending verifications
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {verifications.map(v => (
                  <Card key={v.id} data-testid={`verification-${v.id}`}>
                    <CardContent className="py-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          {v.user_photo && (
                            <img src={v.user_photo} alt="" className="w-12 h-12 rounded-full object-cover" />
                          )}
                          <div>
                            <p className="font-medium">{v.user_name || 'Unknown'}</p>
                            <p className="text-sm text-[#57534E]">{v.user_email}</p>
                            <Badge variant="outline" className="mt-1">
                              {v.type} - {v.gesture_type}
                            </Badge>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => window.open(v.media_url, '_blank')}
                          >
                            <Eye className="w-4 h-4 mr-1" />
                            View
                          </Button>
                          <Button 
                            size="sm" 
                            className="bg-[#2A9D8F] hover:bg-[#2A9D8F]/90"
                            onClick={() => setActionDialog({ open: true, type: 'verify', item: v })}
                          >
                            <CheckCircle className="w-4 h-4 mr-1" />
                            Approve
                          </Button>
                          <Button 
                            size="sm" 
                            variant="destructive"
                            onClick={() => setActionDialog({ open: true, type: 'reject', item: v })}
                          >
                            <XCircle className="w-4 h-4 mr-1" />
                            Reject
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Reports */}
          <TabsContent value="reports">
            {reports.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center text-[#A8A29E]">
                  No pending reports
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {reports.map(r => (
                  <Card key={r.id} data-testid={`report-${r.id}`}>
                    <CardContent className="py-4">
                      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge variant="destructive">{r.reason}</Badge>
                            <span className="text-sm text-[#A8A29E]">
                              {new Date(r.created_at).toLocaleDateString()}
                            </span>
                          </div>
                          <p className="text-sm text-[#57534E] mb-2">{r.details}</p>
                          <div className="text-xs text-[#A8A29E]">
                            <span>Reported by: {r.reporter_name || r.reporter_email}</span>
                          </div>
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          <div className="flex items-center gap-2">
                            {r.reported_photo && (
                              <img src={r.reported_photo} alt="" className="w-10 h-10 rounded-full object-cover" />
                            )}
                            <div className="text-right">
                              <p className="font-medium">{r.reported_name}</p>
                              <p className="text-xs text-[#A8A29E]">{r.reported_email}</p>
                              {r.reported_shadow_banned && (
                                <Badge variant="outline" className="text-xs">Shadow Banned</Badge>
                              )}
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => setActionDialog({ open: true, type: 'user_action', item: r })}
                            >
                              <Ban className="w-4 h-4 mr-1" />
                              Take Action
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => handleReport(r.id, 'dismissed')}
                            >
                              Dismiss
                            </Button>
                          </div>
                        </div>
                      </div>
                      {r.evidence_messages?.length > 0 && (
                        <div className="mt-4 p-3 bg-stone-50 rounded-lg">
                          <p className="text-xs font-medium mb-2">Evidence Messages:</p>
                          <div className="space-y-1 text-xs text-[#57534E]">
                            {r.evidence_messages.slice(0, 5).map((msg, i) => (
                              <p key={i}>
                                <span className="font-medium">{msg.sender_name}:</span> {msg.content}
                              </p>
                            ))}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Audit Log */}
          <TabsContent value="audit">
            <Card>
              <CardContent className="p-0">
                <div className="divide-y divide-stone-100">
                  {auditLog.map(action => (
                    <div key={action.id} className="p-4 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Activity className="w-4 h-4 text-[#A8A29E]" />
                        <div>
                          <p className="text-sm">
                            <span className="font-medium">{action.action_type}</span>
                            {action.reason && ` - ${action.reason}`}
                          </p>
                          <p className="text-xs text-[#A8A29E]">
                            by {action.admin_email} • {new Date(action.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Action Dialog */}
      <Dialog open={actionDialog.open} onOpenChange={(open) => setActionDialog({ ...actionDialog, open })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {actionDialog.type === 'verify' && 'Approve Verification'}
              {actionDialog.type === 'reject' && 'Reject Verification'}
              {actionDialog.type === 'user_action' && 'Take Action on User'}
            </DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <Textarea
              placeholder="Add notes (optional)"
              value={notes}
              onChange={e => setNotes(e.target.value)}
              className="mb-4"
            />
            {actionDialog.type === 'user_action' && (
              <div className="space-y-2">
                <Button 
                  className="w-full" 
                  variant="outline"
                  onClick={() => handleUserAction(actionDialog.item?.reported_user_id, 'warn', notes)}
                >
                  Warn User
                </Button>
                <Button 
                  className="w-full" 
                  variant="outline"
                  onClick={() => handleUserAction(actionDialog.item?.reported_user_id, 'restrict_messaging', notes)}
                >
                  Restrict Messaging
                </Button>
                <Button 
                  className="w-full" 
                  variant="outline"
                  onClick={() => handleUserAction(actionDialog.item?.reported_user_id, 'shadow_ban', notes)}
                >
                  Shadow Ban
                </Button>
                <Button 
                  className="w-full" 
                  variant="destructive"
                  onClick={() => handleUserAction(actionDialog.item?.reported_user_id, 'suspend', notes)}
                >
                  Suspend Account
                </Button>
              </div>
            )}
          </div>
          {(actionDialog.type === 'verify' || actionDialog.type === 'reject') && (
            <DialogFooter>
              <Button variant="outline" onClick={() => setActionDialog({ open: false, type: null, item: null })}>
                Cancel
              </Button>
              <Button 
                onClick={() => handleVerification(
                  actionDialog.item?.id, 
                  actionDialog.type === 'verify' ? 'APPROVED' : 'REJECTED'
                )}
                className={actionDialog.type === 'verify' ? 'bg-[#2A9D8F]' : 'bg-red-500'}
              >
                {actionDialog.type === 'verify' ? 'Approve' : 'Reject'}
              </Button>
            </DialogFooter>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
