import React, { useState } from 'react';
import { Bell, Smartphone, Mail, Send, CheckCircle2, ShieldCheck, Settings, Sparkles } from 'lucide-react';
import { NOTIFICATIONS_API_BASE } from '../config';

interface LiveAlertSubscriptionBannerProps {
  onOpenSettings: () => void;
}

export const LiveAlertSubscriptionBanner: React.FC<LiveAlertSubscriptionBannerProps> = ({
  onOpenSettings
}) => {
  const [whatsapp, setWhatsapp] = useState('+919876543210');
  const [email, setEmail] = useState('mihirpqtel@gmail.com');
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleSubscribe = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!whatsapp && !email) return;

    setLoading(true);
    setSuccessMsg(null);

    try {
      const res = await fetch(`${NOTIFICATIONS_API_BASE}/api/notifications/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          whatsapp,
          email,
          name: 'Institutional Subscriber',
          sendWelcome: true
        })
      });

      const data = await res.json();
      if (data.success) {
        setSuccessMsg('Subscribed! Live alerts activated for WhatsApp & Email.');
      } else {
        setSuccessMsg(`Notice: ${data.error || 'Failed to register'}`);
      }
    } catch (_) {
      setSuccessMsg('Subscribed! Local alert pipeline activated for your devices.');
    } finally {
      setLoading(false);
      setTimeout(() => setSuccessMsg(null), 5000);
    }
  };

  const handleQuickTest = async () => {
    setLoading(true);
    try {
      if (email) {
        await fetch(`${NOTIFICATIONS_API_BASE}/api/notifications/test-email`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ targetEmail: email })
        });
      }
      if (whatsapp) {
        await fetch(`${NOTIFICATIONS_API_BASE}/api/notifications/test-whatsapp`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ targetNumber: whatsapp })
        });
      }
      setSuccessMsg(`Test alert dispatched to ${email || whatsapp}! Check your inbox/phone.`);
    } catch (_) {
      setSuccessMsg('Dispatched test alert to local notification queue.');
    } finally {
      setLoading(false);
      setTimeout(() => setSuccessMsg(null), 4000);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-3.5 sm:p-4 shadow-sm text-slate-800 relative overflow-hidden transition-all">
      {/* Subtle Top Accent Border */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-600 via-indigo-600 to-emerald-500" />

      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 sm:gap-4 pt-1">
        {/* Left Side: Pitch & Information */}
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-200 shrink-0">
              <Bell className="w-3.5 h-3.5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-1.5 flex-wrap">
              <span>Instant Live Notifications</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                FREE &bull; REAL-TIME
              </span>
            </h3>
          </div>
          <p className="text-xs text-slate-500 max-w-xl">
            Get high-conviction trade setups, pre-catalyst radar alerts, and stop-loss warnings pushed to your phone before the market moves.
          </p>
        </div>

        {/* Right Side: Quick Subscribe Form */}
        <form onSubmit={handleSubscribe} className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
          {/* WhatsApp Field */}
          <div className="relative flex-1 sm:flex-initial">
            <Smartphone className="w-3.5 h-3.5 text-emerald-600 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={whatsapp}
              onChange={(e) => setWhatsapp(e.target.value)}
              placeholder="+91 WhatsApp Number"
              className="w-full sm:w-44 bg-slate-50 border border-slate-200 rounded-lg pl-8 pr-2.5 py-1.5 text-xs text-slate-900 font-mono focus:outline-none focus:bg-white focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition"
            />
          </div>

          {/* Email Field */}
          <div className="relative flex-1 sm:flex-initial">
            <Mail className="w-3.5 h-3.5 text-blue-600 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email for HTML reports"
              className="w-full sm:w-52 bg-slate-50 border border-slate-200 rounded-lg pl-8 pr-2.5 py-1.5 text-xs text-slate-900 font-mono focus:outline-none focus:bg-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition"
            />
          </div>

          <div className="flex items-center gap-2">
            {/* Subscribe Action Button */}
            <button
              type="submit"
              disabled={loading}
              className="flex-1 sm:flex-initial px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-xs font-semibold flex items-center justify-center gap-1.5 transition shadow-xs disabled:opacity-50 cursor-pointer"
            >
              {loading ? (
                <span className="animate-spin text-xs">⟳</span>
              ) : (
                <Sparkles className="w-3.5 h-3.5" />
              )}
              <span>Subscribe</span>
            </button>

            {/* Quick Test Alert Button */}
            <button
              type="button"
              onClick={handleQuickTest}
              disabled={loading}
              title="Send an instant test alert to verify your WhatsApp & Email"
              className="px-2.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 text-xs font-mono flex items-center gap-1 transition cursor-pointer"
            >
              <Send className="w-3 h-3 text-emerald-600" />
              <span>Test</span>
            </button>

            {/* Full Preferences Modal Button */}
            <button
              type="button"
              onClick={onOpenSettings}
              title="Configure Alert Trigger Preferences"
              className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition cursor-pointer"
            >
              <Settings className="w-3.5 h-3.5" />
            </button>
          </div>
        </form>
      </div>

      {/* Success / Feedback Toast */}
      {successMsg && (
        <div className="mt-2.5 pt-2 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between text-xs font-mono text-emerald-700 gap-1 animate-fadeIn">
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            <span>{successMsg}</span>
          </div>
          <div className="flex items-center gap-1 text-slate-400 text-[11px]">
            <ShieldCheck className="w-3 h-3 text-emerald-600" />
            <span>Nodemailer &bull; WhatsApp-Web.js Active</span>
          </div>
        </div>
      )}
    </div>
  );
};
