const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '.env') });
require('dotenv').config({ path: path.resolve(__dirname, '../../.env') });

const WhatsAppNotificationService = require('./whatsapp_service');
const EmailNotificationService = require('./email_service');

const app = express();
const PORT = process.env.NOTIFICATION_PORT || 5001;
const LOG_FILE = path.resolve(__dirname, '../../data/dispatched_alerts_log.json');
const SUBSCRIBERS_FILE = path.resolve(__dirname, '../../data/notification_subscribers.json');

const crypto = require('crypto');

app.use(cors());
app.use(express.json());

const ADMIN_SECRET_KEY = process.env.ADMIN_SECRET_KEY || 'admin@institutional2026';

// Constant-time token comparison to eliminate timing side-channel attacks
function safeCompareTokens(provided, actual) {
  if (!provided || !actual) return false;
  const bufA = Buffer.from(String(provided));
  const bufB = Buffer.from(String(actual));
  if (bufA.length !== bufB.length) return false;
  return crypto.timingSafeEqual(bufA, bufB);
}

// In-Memory Brute-Force Defense: Max 5 failed attempts per IP with 15-minute lockout
const authFailedAttempts = new Map(); // ip -> { count: number, lockedUntil: number | null }
const MAX_LOGIN_ATTEMPTS = 5;
const LOCKOUT_DURATION_MS = 15 * 60 * 1000; // 15 Minutes

function checkLockoutStatus(ip) {
  const record = authFailedAttempts.get(ip);
  if (!record) return { isLocked: false, remaining: MAX_LOGIN_ATTEMPTS };
  if (record.lockedUntil && Date.now() < record.lockedUntil) {
    const minutesLeft = Math.ceil((record.lockedUntil - Date.now()) / 60000);
    return { isLocked: true, minutesLeft, remaining: 0 };
  }
  if (record.lockedUntil && Date.now() >= record.lockedUntil) {
    authFailedAttempts.delete(ip);
    return { isLocked: false, remaining: MAX_LOGIN_ATTEMPTS };
  }
  return { isLocked: false, remaining: Math.max(0, MAX_LOGIN_ATTEMPTS - record.count) };
}

function recordAuthFailure(ip) {
  const record = authFailedAttempts.get(ip) || { count: 0, lockedUntil: null };
  record.count += 1;
  if (record.count >= MAX_LOGIN_ATTEMPTS) {
    record.lockedUntil = Date.now() + LOCKOUT_DURATION_MS;
    console.warn(`[SECURITY ALERT] IP ${ip} exceeded ${MAX_LOGIN_ATTEMPTS} failed admin attempts. Locked out for 15 minutes.`);
  }
  authFailedAttempts.set(ip, record);
}

function clearAuthFailures(ip) {
  authFailedAttempts.delete(ip);
}

// Administrator Authorization Middleware
function requireAdminAuth(req, res, next) {
  const token = req.headers['x-admin-token'] || 
    (req.headers['authorization'] && req.headers['authorization'].replace(/^Bearer\s+/i, ''));
  if (!token || !safeCompareTokens(token, ADMIN_SECRET_KEY)) {
    return res.status(401).json({
      success: false,
      error: 'UNAUTHORIZED: Valid cryptographic administrator token required.'
    });
  }
  next();
}

// Admin Auth Verification Endpoint with Anti-Brute-Force Lockout
app.post('/api/admin/auth/verify', (req, res) => {
  const clientIp = req.ip || req.headers['x-forwarded-for'] || req.connection.remoteAddress || '127.0.0.1';
  const { isLocked, minutesLeft, remaining } = checkLockoutStatus(clientIp);

  if (isLocked) {
    return res.status(429).json({
      success: false,
      authorized: false,
      error: `Security Lockout Active: Too many failed administrative attempts. Terminal locked for ${minutesLeft} minutes.`
    });
  }

  const { token } = req.body;
  if (token && safeCompareTokens(token, ADMIN_SECRET_KEY)) {
    clearAuthFailures(clientIp);
    console.log(`[ADMIN AUDIT] Master Administrator successfully authenticated from IP: ${clientIp}`);
    return res.json({ success: true, authorized: true, message: 'Master Administrator authenticated. Console unlocked.' });
  }

  recordAuthFailure(clientIp);
  const updatedStatus = checkLockoutStatus(clientIp);
  if (updatedStatus.isLocked) {
    return res.status(429).json({
      success: false,
      authorized: false,
      error: `Maximum attempts exceeded. IP locked out for 15 minutes.`
    });
  }

  return res.status(401).json({
    success: false,
    authorized: false,
    error: `Invalid master administrator key. Access denied. (${updatedStatus.remaining} attempts remaining before 15m lockout)`
  });
});

// Initialize Services
const waService = new WhatsAppNotificationService();
const emailService = new EmailNotificationService();

// Helper to normalize phone numbers
function normalizePhoneNumber(raw) {
  if (!raw) return '';
  let clean = String(raw).replace(/[\s\-\(\)]/g, '').trim();
  if (!clean.startsWith('+')) {
    if (clean.length === 10) {
      clean = '+91' + clean;
    } else {
      clean = '+' + clean;
    }
  }
  return clean;
}

// Helper to log dispatched alert with 90-day rolling retention policy
function recordDispatchedAlert(alertObj) {
  try {
    let history = [];
    if (fs.existsSync(LOG_FILE)) {
      history = JSON.parse(fs.readFileSync(LOG_FILE, 'utf-8'));
    }
    history.unshift({
      id: `ALT_${Date.now()}`,
      timestamp: new Date().toISOString(),
      retention_policy: '90_DAYS',
      ...alertObj
    });

    // 90-Day Strict Retention Filter (7,776,000,000 ms)
    const NINETY_DAYS_MS = 90 * 24 * 60 * 60 * 1000;
    const cutoff = Date.now() - NINETY_DAYS_MS;
    const prunedHistory = history.filter(item => {
      const ts = new Date(item.timestamp).getTime();
      return !isNaN(ts) && ts >= cutoff;
    });

    fs.writeFileSync(LOG_FILE, JSON.stringify(prunedHistory, null, 2), 'utf-8');
  } catch (e) {
    console.warn('[LOG ERROR] Could not persist alert:', e.message);
  }
}

// Helper to load subscribers database
function loadSubscribersData() {
  if (fs.existsSync(SUBSCRIBERS_FILE)) {
    try {
      const data = JSON.parse(fs.readFileSync(SUBSCRIBERS_FILE, 'utf-8'));
      if (data && Array.isArray(data.subscribers)) {
        return data;
      }
    } catch (_) {}
  }
  
  // Default initial subscriber seed
  const defaultData = {
    subscribers: [
      {
        id: 'SUB_001_PRIMARY',
        name: 'Primary Trader',
        whatsapp: '+919876543210',
        email: 'mihirpqtel@gmail.com',
        active: true,
        created_at: new Date().toISOString(),
        preferences: {
          preCatalystRadar: true,
          liveSignals: true,
          doNotChaseAlerts: true,
          stopLossWarnings: true,
          dailyBriefing: true
        }
      }
    ]
  };
  try {
    fs.mkdirSync(path.dirname(SUBSCRIBERS_FILE), { recursive: true });
    fs.writeFileSync(SUBSCRIBERS_FILE, JSON.stringify(defaultData, null, 2), 'utf-8');
  } catch (_) {}
  return defaultData;
}

function saveSubscribersData(data) {
  fs.mkdirSync(path.dirname(SUBSCRIBERS_FILE), { recursive: true });
  fs.writeFileSync(SUBSCRIBERS_FILE, JSON.stringify(data, null, 2), 'utf-8');
}

// 1. Overall Status Endpoint
app.get('/api/notifications/status', (req, res) => {
  const subData = loadSubscribersData();
  const activeSubs = subData.subscribers.filter(s => s.active !== false);
  
  const allWa = [...new Set(activeSubs.map(s => s.whatsapp).filter(Boolean))];
  const allEmails = [...new Set(activeSubs.map(s => s.email).filter(Boolean))];

  res.json({
    status: 'ONLINE',
    service: 'Institutional Multi-Channel Notification Hub',
    subscribers_count: activeSubs.length,
    whatsapp: waService.getStatus(),
    email: emailService.getStatus(),
    config: {
      whatsappNumbers: allWa,
      emailRecipients: allEmails,
      subscribers: activeSubs,
      preferences: {
        preCatalystRadar: true,
        liveSignals: true,
        doNotChaseAlerts: true,
        stopLossWarnings: true,
        dailyBriefing: true
      }
    },
    serverTime: new Date().toISOString()
  });
});

// 2. WhatsApp QR Code Endpoint
app.get('/api/notifications/qr', (req, res) => {
  res.json(waService.getQrData());
});

// 3. User Subscription Endpoint (User enters WhatsApp & Email on Platform)
app.post('/api/notifications/subscribe', async (req, res) => {
  const { name, whatsapp, email, preferences, sendWelcome } = req.body;

  if (!whatsapp && !email) {
    return res.status(400).json({ success: false, error: 'At least WhatsApp number or Email address is required.' });
  }

  const cleanWa = normalizePhoneNumber(whatsapp);
  const cleanEmail = email ? email.trim().toLowerCase() : '';

  const subData = loadSubscribersData();
  let existingIndex = -1;

  // Search if subscriber already exists
  if (cleanWa) {
    existingIndex = subData.subscribers.findIndex(s => s.whatsapp === cleanWa);
  }
  if (existingIndex === -1 && cleanEmail) {
    existingIndex = subData.subscribers.findIndex(s => s.email === cleanEmail);
  }

  const subRecord = {
    id: existingIndex >= 0 ? subData.subscribers[existingIndex].id : `SUB_${Date.now()}`,
    name: name || 'Institutional Trader',
    whatsapp: cleanWa,
    email: cleanEmail,
    active: true,
    updated_at: new Date().toISOString(),
    preferences: preferences || {
      preCatalystRadar: true,
      liveSignals: true,
      doNotChaseAlerts: true,
      stopLossWarnings: true,
      dailyBriefing: true
    }
  };

  if (existingIndex >= 0) {
    subData.subscribers[existingIndex] = { ...subData.subscribers[existingIndex], ...subRecord };
  } else {
    subRecord.created_at = new Date().toISOString();
    subData.subscribers.push(subRecord);
  }

  saveSubscribersData(subData);

  // Send optional welcome notifications
  let welcomeReport = { whatsapp: null, email: null };
  if (sendWelcome !== false) {
    if (cleanWa) {
      const waMsg = 
`⚡ *INSTITUTIONAL AI NEWS NOTIFICATION SUBSCRIBED*
• *Status:* LIVE ACTIVATED
• *WhatsApp Number:* ${cleanWa}
• *Target:* Pre-Catalyst Radar & High-Conviction T+1 Signals
• *Time:* ${new Date().toLocaleTimeString('en-IN')} IST

✅ You are now connected to the sub-second institutional stream. You will receive entry targets, stop-losses, and Kelly capital sizing before the market moves!`;
      try {
        welcomeReport.whatsapp = await waService.sendTextMessage(cleanWa, waMsg);
      } catch (err) {
        welcomeReport.whatsapp = { error: err.message };
      }
    }

    if (cleanEmail) {
      try {
        welcomeReport.email = await emailService.sendTestEmail(cleanEmail);
      } catch (err) {
        welcomeReport.email = { error: err.message };
      }
    }
  }

  recordDispatchedAlert({
    channel: 'SUBSCRIPTION_UPDATE',
    type: 'USER_OPT_IN',
    subscriber: subRecord,
    welcomeReport
  });

  res.json({
    success: true,
    message: 'Subscriber registered successfully for live multi-channel alerts.',
    subscriber: subRecord,
    welcomeReport
  });
});

// 4. List All Active Subscribers (Admin Only)
app.get('/api/notifications/subscribers', requireAdminAuth, (req, res) => {
  const subData = loadSubscribersData();
  res.json({
    total: subData.subscribers.length,
    active_count: subData.subscribers.filter(s => s.active !== false).length,
    subscribers: subData.subscribers
  });
});

// 5. Unsubscribe / Remove Subscriber
app.post('/api/notifications/unsubscribe', (req, res) => {
  const { id, whatsapp, email } = req.body;
  const subData = loadSubscribersData();
  
  subData.subscribers = subData.subscribers.map(s => {
    if ((id && s.id === id) || (whatsapp && s.whatsapp === normalizePhoneNumber(whatsapp)) || (email && s.email === email.toLowerCase())) {
      return { ...s, active: false };
    }
    return s;
  });

  saveSubscribersData(subData);
  res.json({ success: true, message: 'Subscriber deactivated.' });
});

// 5b. Admin: Delete Subscriber Permanently
app.delete('/api/notifications/subscribers/:id', requireAdminAuth, (req, res) => {
  const { id } = req.params;
  const subData = loadSubscribersData();
  const initialLen = subData.subscribers.length;
  subData.subscribers = subData.subscribers.filter(s => s.id !== id);
  saveSubscribersData(subData);
  res.json({
    success: true,
    message: subData.subscribers.length < initialLen ? 'Subscriber deleted permanently.' : 'Subscriber not found.'
  });
});

// 5c. Admin: Toggle Subscriber Active / Paused State
app.post('/api/notifications/subscribers/:id/toggle', requireAdminAuth, (req, res) => {
  const { id } = req.params;
  const subData = loadSubscribersData();
  const target = subData.subscribers.find(s => s.id === id);
  if (!target) {
    return res.status(404).json({ success: false, error: 'Subscriber not found.' });
  }
  target.active = !target.active;
  target.updated_at = new Date().toISOString();
  saveSubscribersData(subData);
  res.json({ success: true, subscriber: target });
});

// 5d. Admin: Send Direct Test Notification to Specific Subscriber
app.post('/api/notifications/subscribers/:id/test', requireAdminAuth, async (req, res) => {
  const { id } = req.params;
  const { channel } = req.body; // 'WHATSAPP', 'EMAIL', or 'BOTH'
  const subData = loadSubscribersData();
  const sub = subData.subscribers.find(s => s.id === id);
  if (!sub) {
    return res.status(404).json({ success: false, error: 'Subscriber not found.' });
  }

  const results = { whatsapp: null, email: null };

  if ((channel === 'WHATSAPP' || channel === 'BOTH' || !channel) && sub.whatsapp) {
    const waMsg = 
`⚡ *DIRECT SUBSCRIBER TEST ALERT*
• *Subscriber:* ${sub.name}
• *Target WhatsApp:* ${sub.whatsapp}
• *System Status:* ONLINE (13.04ms Pipeline)
• *Dispatched by:* Institutional Admin Panel
• *Time:* ${new Date().toLocaleTimeString('en-IN')} IST

✅ Connection to your WhatsApp account is verified and ready for live trade signals.`;
    try {
      results.whatsapp = await waService.sendTextMessage(sub.whatsapp, waMsg);
    } catch (err) {
      results.whatsapp = { error: err.message };
    }
  }

  if ((channel === 'EMAIL' || channel === 'BOTH' || !channel) && sub.email) {
    try {
      results.email = await emailService.sendTestEmail(sub.email);
    } catch (err) {
      results.email = { error: err.message };
    }
  }

  recordDispatchedAlert({
    channel: 'DIRECT_TEST',
    type: 'SUBSCRIBER_PING',
    subscriberId: sub.id,
    subscriberName: sub.name,
    results
  });

  res.json({ success: true, subscriber: sub, results });
});

// 6. Test WhatsApp Endpoint
app.post('/api/notifications/test-whatsapp', requireAdminAuth, async (req, res) => {
  const { targetNumber } = req.body;
  const num = normalizePhoneNumber(targetNumber) || waService.defaultRecipients[0];
  
  const testMessage = 
`⚡ *TEST NOTIFICATION: Institutional AI News Impact Engine*
• *System Status:* ONLINE (13.04ms Pipeline)
• *WhatsApp Web Gateway:* VERIFIED
• *Recipient:* ${num}
• *Time:* ${new Date().toLocaleTimeString('en-IN')} IST

✅ You are now subscribed to receive instant Pre-Catalyst Radar alerts and high-conviction trade entries!`;

  const result = await waService.sendTextMessage(num, testMessage);
  recordDispatchedAlert({
    channel: 'WHATSAPP',
    type: 'TEST_MESSAGE',
    recipient: num,
    result
  });

  res.json({
    success: true,
    targetNumber: num,
    result
  });
});

// 7. Test Email Endpoint
app.post('/api/notifications/test-email', requireAdminAuth, async (req, res) => {
  const { targetEmail } = req.body;
  const email = (targetEmail ? targetEmail.trim().toLowerCase() : null) || emailService.defaultRecipients[0];

  const result = await emailService.sendTestEmail(email);
  recordDispatchedAlert({
    channel: 'EMAIL',
    type: 'TEST_EMAIL',
    recipient: email,
    result
  });

  res.json({
    success: result.success,
    targetEmail: email,
    result
  });
});

// 8. Broadcast Signal to All Subscribers (Called by Python Engine or UI)
app.post('/api/notifications/broadcast-signal', requireAdminAuth, async (req, res) => {
  const { signal, targetNumbers, targetEmails, channels } = req.body;

  if (!signal) {
    return res.status(400).json({ error: 'Missing required `signal` payload.' });
  }

  const selectedChannels = channels || ['WHATSAPP', 'EMAIL'];
  const subData = loadSubscribersData();
  const activeSubs = subData.subscribers.filter(s => s.active !== false);

  // Extract recipients from subscriber list or overrides
  let waRecipients = targetNumbers;
  if (!waRecipients || waRecipients.length === 0) {
    waRecipients = [...new Set(
      activeSubs
        .filter(s => s.preferences?.liveSignals !== false)
        .map(s => s.whatsapp)
        .filter(Boolean)
    )];
  }

  let emRecipients = targetEmails;
  if (!emRecipients || emRecipients.length === 0) {
    emRecipients = [...new Set(
      activeSubs
        .filter(s => s.preferences?.liveSignals !== false)
        .map(s => s.email)
        .filter(Boolean)
    )];
  }

  // Fallbacks if subscriber list was empty
  if (waRecipients.length === 0) waRecipients = waService.defaultRecipients;
  if (emRecipients.length === 0) emRecipients = emailService.defaultRecipients;

  const responseReport = {
    signalId: signal.id || signal.symbol,
    symbol: signal.symbol,
    dispatchedAt: new Date().toISOString(),
    channels: {},
    recipientsCount: {
      whatsapp: waRecipients.length,
      email: emRecipients.length
    }
  };

  // WhatsApp Dispatch to all recipients
  if (selectedChannels.includes('WHATSAPP') && waRecipients.length > 0) {
    const waRes = await waService.broadcastSignal(signal, waRecipients);
    responseReport.channels.whatsapp = waRes;
  }

  // Email Dispatch to all recipients
  if (selectedChannels.includes('EMAIL') && emRecipients.length > 0) {
    const emRes = await emailService.sendSignalEmail(signal, emRecipients);
    responseReport.channels.email = emRes;
  }

  recordDispatchedAlert({
    channel: 'MULTI_CHANNEL',
    type: 'SIGNAL_BROADCAST',
    symbol: signal.symbol,
    headline: signal.headline,
    report: responseReport
  });

  res.json({
    success: true,
    message: `Alert broadcast successfully for ${signal.symbol} to ${waRecipients.length} WhatsApp & ${emRecipients.length} Email subscribers`,
    report: responseReport
  });
});

// 9. Recent Dispatched History
app.get('/api/notifications/history', (req, res) => {
  try {
    if (fs.existsSync(LOG_FILE)) {
      const logs = JSON.parse(fs.readFileSync(LOG_FILE, 'utf-8'));
      return res.json({ total: logs.length, history: logs });
    }
  } catch (_) {}
  res.json({ total: 0, history: [] });
});

// 10. Config Get / Save
app.get('/api/notifications/config', (req, res) => {
  res.json(loadSubscribersData());
});

app.post('/api/notifications/config', (req, res) => {
  const newConfig = req.body;
  try {
    saveSubscribersData(newConfig);
    res.json({ success: true, config: newConfig });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// 11. Admin: Update SMTP Credentials Dynamically
app.post('/api/notifications/smtp-config', requireAdminAuth, (req, res) => {
  const { host, port, user, pass, from } = req.body;
  if (!host || !user) {
    return res.status(400).json({ success: false, error: 'Host and user are required.' });
  }

  // Update process.env
  process.env.SMTP_HOST = host;
  process.env.SMTP_PORT = String(port || '465');
  process.env.SMTP_USER = user;
  if (pass && pass.trim() !== '' && pass !== 'KEEP_EXISTING') {
    process.env.SMTP_PASS = pass;
  }
  if (from) process.env.SMTP_FROM = from;

  // Persist to .env file
  const envPath = path.resolve(__dirname, '.env');
  let envLines = [];
  if (fs.existsSync(envPath)) {
    envLines = fs.readFileSync(envPath, 'utf-8').split('\n');
  }

  const updateOrAdd = (key, val) => {
    const idx = envLines.findIndex(l => l.startsWith(`${key}=`));
    if (idx >= 0) {
      envLines[idx] = `${key}="${val}"`;
    } else {
      envLines.push(`${key}="${val}"`);
    }
  };

  updateOrAdd('SMTP_HOST', host);
  updateOrAdd('SMTP_PORT', String(port || '465'));
  updateOrAdd('SMTP_USER', user);
  if (pass && pass.trim() !== '' && pass !== 'KEEP_EXISTING') {
    updateOrAdd('SMTP_PASS', pass);
  }
  if (from) updateOrAdd('SMTP_FROM', from);

  try {
    fs.writeFileSync(envPath, envLines.join('\n'), 'utf-8');
  } catch (err) {
    console.warn('[ENV SAVE WARNING]', err.message);
  }

  // Re-initialize email transporter
  emailService.initTransporter();

  res.json({
    success: true,
    message: 'SMTP settings updated securely and transport re-initialized.',
    emailStatus: emailService.getStatus()
  });
});

// 12. Admin: Clear Alert Dispatch Log
app.post('/api/notifications/history/clear', requireAdminAuth, (req, res) => {
  try {
    fs.writeFileSync(LOG_FILE, JSON.stringify([], null, 2), 'utf-8');
    res.json({ success: true, message: 'Dispatched alert logs cleared.' });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// 13. Admin: Restart WhatsApp Client Session
app.post('/api/notifications/restart-whatsapp', requireAdminAuth, async (req, res) => {
  try {
    if (waService.client) {
      try { await waService.client.destroy(); } catch (_) {}
    }
    waService.isInitializing = false;
    waService.initClient();
    res.json({ success: true, message: 'WhatsApp client re-initialization triggered.' });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// 14. Admin: Full System Overview Endpoint
app.get('/api/notifications/admin-overview', requireAdminAuth, (req, res) => {
  const subData = loadSubscribersData();
  const activeSubs = subData.subscribers.filter(s => s.active !== false);
  let historyCount = 0;
  let lastDispatch = null;
  try {
    if (fs.existsSync(LOG_FILE)) {
      const logs = JSON.parse(fs.readFileSync(LOG_FILE, 'utf-8'));
      historyCount = logs.length;
      if (logs.length > 0) lastDispatch = logs[0];
    }
  } catch (_) {}

  res.json({
    status: 'ONLINE',
    subscribers: {
      total: subData.subscribers.length,
      active: activeSubs.length,
      inactive: subData.subscribers.length - activeSubs.length
    },
    gateways: {
      whatsapp: waService.getStatus(),
      email: emailService.getStatus()
    },
    history: {
      total_dispatches: historyCount,
      last_dispatch: lastDispatch
    },
    server_time: new Date().toISOString()
  });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`[INSTITUTIONAL NOTIFICATION HUB] Running on http://127.0.0.1:${PORT}`);
  console.log(`[ENDPOINTS]`);
  console.log(`  - Status:      GET  http://127.0.0.1:${PORT}/api/notifications/status`);
  console.log(`  - Subscribe:   POST http://127.0.0.1:${PORT}/api/notifications/subscribe`);
  console.log(`  - Subscribers: GET  http://127.0.0.1:${PORT}/api/notifications/subscribers`);
  console.log(`  - QR Code:     GET  http://127.0.0.1:${PORT}/api/notifications/qr`);
  console.log(`  - Broadcast:   POST http://127.0.0.1:${PORT}/api/notifications/broadcast-signal`);
});
