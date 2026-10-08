import React, { useState, useEffect } from 'react';
import {
  X,
  Bell,
  CheckCircle2,
  Smartphone,
  ShieldCheck,
  Zap,
  Sliders,
  Sparkles,
  Lock
} from 'lucide-react';

interface NotificationSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const NotificationSettingsModal: React.FC<NotificationSettingsModalProps> = ({
  isOpen,
  onClose
}) => {
  const [userName, setUserName] = useState<string>('');
  const [targetNumber, setTargetNumber] = useState<string>('');
  const [targetEmail, setTargetEmail] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [feedbackNotice, setFeedbackNotice] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Preference toggles
  const [prefPreCatalyst, setPrefPreCatalyst] = useState<boolean>(true);
  const [prefHighConviction, setPrefHighConviction] = useState<boolean>(true);
  const [prefDoNotChase, setPrefDoNotChase] = useState<boolean>(true);
  const [prefStopLoss, setPrefStopLoss] = useState<boolean>(true);
  const [prefMorningBrief, setPrefMorningBrief] = useState<boolean>(true);
  const [prefTargetHits, setPrefTargetHits] = useState<boolean>(true);

  // Pre-load default values or existing session
  useEffect(() => {
    if (isOpen) {
      const savedNumber = localStorage.getItem('user_alert_wa') || '';
      const savedEmail = localStorage.getItem('user_alert_email') || '';
      const savedName = localStorage.getItem('user_alert_name') || '';
      if (savedNumber) setTargetNumber(savedNumber);
      if (savedEmail) setTargetEmail(savedEmail);
      if (savedName) setUserName(savedName);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const triggerNotice = (type: 'success' | 'error', message: string) => {
    setFeedbackNotice({ type, message });
    setTimeout(() => setFeedbackNotice(null), 4500);
  };

  // Subscribe Handler
  const handleSubscribe = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!targetNumber.trim() && !targetEmail.trim()) {
      triggerNotice('error', 'Please provide at least a WhatsApp mobile number or an Email address.');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:5001/api/notifications/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: userName.trim() || 'Institutional Trader',
          whatsapp: targetNumber.trim(),
          email: targetEmail.trim(),
          sendWelcome: true,
          preferences: {
            preCatalystRadar: prefPreCatalyst,
            liveSignals: prefHighConviction,
            doNotChaseAlerts: prefDoNotChase,
            stopLossWarnings: prefStopLoss,
            dailyBriefing: prefMorningBrief,
            targetHits: prefTargetHits
          }
        })
      });

      const data = await res.json();
      if (data.success) {
        localStorage.setItem('user_alert_wa', targetNumber.trim());
        localStorage.setItem('user_alert_email', targetEmail.trim());
        localStorage.setItem('user_alert_name', userName.trim());
        triggerNotice(
          'success',
          `Successfully registered! Live trade alerts are now active for ${targetNumber.trim() || targetEmail.trim()}.`
        );
      } else {
        triggerNotice('error', data.error || 'Failed to activate live alerts. Please try again.');
      }
    } catch (err: any) {
      triggerNotice('error', `Connection error: ${err.message || 'Notification service temporarily unreachable.'}`);
    } finally {
      setLoading(false);
    }
  };

  // Quick Test WhatsApp
  const handleTestWhatsApp = async () => {
    if (!targetNumber.trim()) {
      triggerNotice('error', 'Please enter your WhatsApp mobile number first.');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:5001/api/notifications/test-whatsapp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ targetNumber: targetNumber.trim() })
      });
      const data = await res.json();
      if (data.success) {
        triggerNotice('success', `Test WhatsApp ping dispatched to ${targetNumber.trim()}!`);
      } else {
        triggerNotice('error', data.error || 'WhatsApp message dispatch failed.');
      }
    } catch (err: any) {
      triggerNotice('error', `Dispatch error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Quick Test Email
  const handleTestEmail = async () => {
    if (!targetEmail.trim()) {
      triggerNotice('error', 'Please enter your email address first.');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:5001/api/notifications/test-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ targetEmail: targetEmail.trim() })
      });
      const data = await res.json();
      if (data.success) {
        triggerNotice('success', `Test HTML email brief dispatched to ${targetEmail.trim()}!`);
      } else {
        triggerNotice('error', data.error || 'Email dispatch failed.');
      }
    } catch (err: any) {
      triggerNotice('error', `Dispatch error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/60 backdrop-blur-xs animate-fadeIn overflow-y-auto">
      <div className="bg-white border border-slate-200 rounded-2xl max-w-xl w-full shadow-2xl overflow-hidden my-auto animate-scaleUp">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 sm:px-6 py-4 border-b border-slate-200 bg-white">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shadow-xs">
              <Bell className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-900 tracking-tight">
                  Get Live Trade Alerts
                </h3>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  REAL-TIME PUSH
                </span>
              </div>
              <p className="text-xs text-slate-500 font-mono">
                Instant WhatsApp & Email notifications within 300ms of corporate filings
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Global Feedback Toast */}
        {feedbackNotice && (
          <div
            className={`py-2 px-5 text-xs font-mono flex items-center gap-2 border-b ${
              feedbackNotice.type === 'success'
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                : 'bg-rose-50 text-rose-800 border-rose-200'
            }`}
          >
            {feedbackNotice.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            ) : (
              <Zap className="w-4 h-4 text-rose-600 shrink-0" />
            )}
            <span>{feedbackNotice.message}</span>
          </div>
        )}

        {/* Modal Body */}
        <div className="p-5 sm:p-6 space-y-5 max-h-[75vh] overflow-y-auto">
          {/* Subscription Form */}
          <form onSubmit={handleSubscribe} className="space-y-4">
            <div className="space-y-3 bg-slate-50 border border-slate-200 rounded-xl p-4">
              <div className="flex items-center justify-between border-b border-slate-200 pb-2.5">
                <span className="text-xs font-bold text-slate-900 font-mono flex items-center gap-1.5">
                  <Smartphone className="w-4 h-4 text-emerald-600" />
                  Your Alert Destination
                </span>
                <span className="text-[10px] text-slate-500 font-mono">
                  Direct Multi-Channel Delivery
                </span>
              </div>

              <div>
                <label className="text-[11px] font-medium text-slate-600 block mb-1">
                  Full Name / Trader Handle (Optional):
                </label>
                <input
                  type="text"
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  placeholder="e.g. Mihir Patel"
                  className="w-full bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-900 font-sans focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-[11px] font-medium text-slate-600">
                    WhatsApp Mobile Number:
                  </label>
                  <span className="text-[10px] text-slate-400 font-mono">Include +91 country code</span>
                </div>
                <div className="flex gap-2">
                  <input
                    type="tel"
                    value={targetNumber}
                    onChange={(e) => setTargetNumber(e.target.value)}
                    placeholder="+91 98765 43210"
                    className="w-full bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-900 font-mono focus:outline-none focus:border-emerald-500"
                  />
                  <button
                    type="button"
                    onClick={handleTestWhatsApp}
                    disabled={loading || !targetNumber.trim()}
                    className="px-3 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 text-xs font-semibold shrink-0 transition disabled:opacity-50 cursor-pointer"
                  >
                    Test WA
                  </button>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-[11px] font-medium text-slate-600">
                    Email Address (HTML Trade Briefs):
                  </label>
                  <span className="text-[10px] text-slate-400 font-mono">Daily & Live Signals</span>
                </div>
                <div className="flex gap-2">
                  <input
                    type="email"
                    value={targetEmail}
                    onChange={(e) => setTargetEmail(e.target.value)}
                    placeholder="trader@gmail.com"
                    className="w-full bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-900 font-mono focus:outline-none focus:border-blue-500"
                  />
                  <button
                    type="button"
                    onClick={handleTestEmail}
                    disabled={loading || !targetEmail.trim()}
                    className="px-3 py-1.5 rounded-lg bg-sky-50 hover:bg-sky-100 text-sky-700 border border-sky-200 text-xs font-semibold shrink-0 transition disabled:opacity-50 cursor-pointer"
                  >
                    Test Mail
                  </button>
                </div>
              </div>
            </div>

            {/* Notification Trigger Preferences */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                <div className="flex items-center gap-1.5">
                  <Sliders className="w-3.5 h-3.5 text-blue-600" />
                  <span className="text-xs font-bold text-slate-900 font-mono">
                    Select Your Notification Triggers
                  </span>
                </div>
                <span className="text-[10px] font-mono text-emerald-700 font-bold">● Free Instant Push</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
                <label className="flex items-center gap-2.5 p-2 rounded-lg bg-white border border-slate-200 cursor-pointer hover:border-slate-300 transition">
                  <input
                    type="checkbox"
                    checked={prefPreCatalyst}
                    onChange={(e) => setPrefPreCatalyst(e.target.checked)}
                    className="rounded text-blue-600 cursor-pointer"
                  />
                  <span className="text-slate-800 font-medium">⚡ Pre-Catalyst Radar</span>
                </label>

                <label className="flex items-center gap-2.5 p-2 rounded-lg bg-white border border-slate-200 cursor-pointer hover:border-slate-300 transition">
                  <input
                    type="checkbox"
                    checked={prefHighConviction}
                    onChange={(e) => setPrefHighConviction(e.target.checked)}
                    className="rounded text-blue-600 cursor-pointer"
                  />
                  <span className="text-slate-800 font-medium">🟢 High Conviction T+1</span>
                </label>

                <label className="flex items-center gap-2.5 p-2 rounded-lg bg-white border border-slate-200 cursor-pointer hover:border-slate-300 transition">
                  <input
                    type="checkbox"
                    checked={prefDoNotChase}
                    onChange={(e) => setPrefDoNotChase(e.target.checked)}
                    className="rounded text-blue-600 cursor-pointer"
                  />
                  <span className="text-slate-800 font-medium">🛡️ DO NOT CHASE Alerts</span>
                </label>

                <label className="flex items-center gap-2.5 p-2 rounded-lg bg-white border border-slate-200 cursor-pointer hover:border-slate-300 transition">
                  <input
                    type="checkbox"
                    checked={prefStopLoss}
                    onChange={(e) => setPrefStopLoss(e.target.checked)}
                    className="rounded text-blue-600 cursor-pointer"
                  />
                  <span className="text-slate-800 font-medium">🛑 Strict 3% Stop-Loss</span>
                </label>

                <label className="flex items-center gap-2.5 p-2 rounded-lg bg-white border border-slate-200 cursor-pointer hover:border-slate-300 transition">
                  <input
                    type="checkbox"
                    checked={prefMorningBrief}
                    onChange={(e) => setPrefMorningBrief(e.target.checked)}
                    className="rounded text-blue-600 cursor-pointer"
                  />
                  <span className="text-slate-800 font-medium">🌅 08:30 AM Briefing</span>
                </label>

                <label className="flex items-center gap-2.5 p-2 rounded-lg bg-white border border-slate-200 cursor-pointer hover:border-slate-300 transition">
                  <input
                    type="checkbox"
                    checked={prefTargetHits}
                    onChange={(e) => setPrefTargetHits(e.target.checked)}
                    className="rounded text-blue-600 cursor-pointer"
                  />
                  <span className="text-slate-800 font-medium">🎯 1-Day Target Hits</span>
                </label>
              </div>
            </div>

            {/* Subscribe Action Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-xs font-mono font-bold flex items-center justify-center gap-2 shadow-sm transition disabled:opacity-50 cursor-pointer"
            >
              {loading ? (
                <>
                  <span className="animate-spin text-sm">⟳</span>
                  <span>Activating Alert Channels...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Activate Live Alerts Now</span>
                </>
              )}
            </button>
          </form>

          {/* Privacy & Institutional SLA Guarantee */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-1.5 font-sans">
            <div className="flex items-center gap-1.5 text-slate-900 font-bold font-mono text-xs">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Institutional Privacy & Speed Guarantee</span>
            </div>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              Alerts are dispatched within 300ms of regulatory exchange filings. Your contact details are stored securely for rolling 90 days with zero third-party marketing or spam.
            </p>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-5 sm:px-6 py-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs font-mono">
          <div className="flex items-center gap-1.5 text-slate-500 text-[11px]">
            <Lock className="w-3.5 h-3.5 text-slate-400" />
            <span>End-to-End Encrypted Notification Pipeline</span>
          </div>
          <button
            onClick={onClose}
            className="px-3.5 py-1.5 rounded-lg bg-slate-200 hover:bg-slate-300 text-slate-700 font-medium transition cursor-pointer text-xs"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
