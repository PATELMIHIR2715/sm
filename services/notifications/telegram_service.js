const https = require('https');
const dns = require('dns');
const path = require('path');

// Ensure Node prioritizes IPv4 to eliminate IPv6 network routing hangs
if (dns.setDefaultResultOrder) {
  try { dns.setDefaultResultOrder('ipv4first'); } catch (_) {}
}

require('dotenv').config({ path: path.resolve(__dirname, '.env') });
require('dotenv').config({ path: path.resolve(__dirname, '../../.env') });
const { formatTelegramAlert, formatTelegramPreCatalystAlert } = require('./notification_templates');

class TelegramNotificationService {
  constructor() {
    this.token = (process.env.TELEGRAM_BOT_TOKEN || '').trim();
    this.channelId = (process.env.TELEGRAM_CHANNEL_ID || '@stockmarketsignalseventbased').trim();
    this.chatId = (process.env.TELEGRAM_CHAT_ID || '-1004309575686').trim();
    this.botUsername = (process.env.TELEGRAM_BOT_USERNAME || 'Stock_market_event_based_bot').trim();
    this.channelLink = (process.env.TELEGRAM_CHANNEL_LINK || 'https://t.me/stockmarketsignalseventbased').trim();
    this.lastDispatchedAt = null;

    if (this.token) {
      console.log(`[TELEGRAM SERVICE] Initialized for bot @${this.botUsername} -> channel ${this.channelId} (${this.chatId})`);
    } else {
      console.warn('[TELEGRAM SERVICE] Telegram bot token not configured in .env');
    }
  }

  getStatus() {
    return {
      status: this.token ? 'CONNECTED_READY' : 'UNCONFIGURED',
      channelId: this.channelId,
      chatId: this.chatId,
      channelTitle: 'Live stock market signals',
      botUsername: this.botUsername,
      channelLink: this.channelLink,
      isConfigured: Boolean(this.token),
      lastDispatchedAt: this.lastDispatchedAt
    };
  }

  _makeRequest(endpoint, payload) {
    return new Promise((resolve, reject) => {
      const data = JSON.stringify(payload);
      const url = new URL(`https://api.telegram.org/bot${this.token}/${endpoint}`);

      const options = {
        hostname: url.hostname,
        port: 443,
        path: url.pathname,
        method: 'POST',
        family: 4,
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(data)
        },
        timeout: 8000
      };

      const req = https.request(options, (res) => {
        let body = '';
        res.on('data', (chunk) => { body += chunk; });
        res.on('end', () => {
          try {
            const parsed = JSON.parse(body);
            resolve(parsed);
          } catch (e) {
            resolve({ ok: false, description: `Malformed JSON response: ${body}` });
          }
        });
      });

      req.on('timeout', () => {
        req.destroy();
        reject(new Error('Telegram API request timed out (8s)'));
      });

      req.on('error', (err) => {
        reject(err);
      });

      req.write(data);
      req.end();
    });
  }

  async sendTextMessage(targetChatId, message, parseMode = 'HTML') {
    const destination = targetChatId || this.chatId || this.channelId;

    if (!this.token) {
      console.warn(`[TELEGRAM SIMULATION] Simulated delivery to ${destination}:\n${message.slice(0, 100)}...`);
      return {
        success: true,
        simulated: true,
        destination,
        messagePreview: message.slice(0, 100) + '...',
        note: 'Telegram bot token missing. Configure TELEGRAM_BOT_TOKEN in .env for live transmission.'
      };
    }

    try {
      const payload = {
        chat_id: destination,
        text: message,
        parse_mode: parseMode,
        disable_web_page_preview: true
      };

      const data = await this._makeRequest('sendMessage', payload);

      if (data.ok) {
        this.lastDispatchedAt = new Date().toISOString();
        console.log(`[TELEGRAM SENT] Successfully delivered to ${destination} (Msg ID: ${data.result.message_id})`);
        return {
          success: true,
          simulated: false,
          messageId: data.result.message_id,
          chatId: destination,
          chatTitle: data.result.chat ? data.result.chat.title : null
        };
      } else {
        console.error(`[TELEGRAM API ERROR] ${data.error_code}: ${data.description}`);
        return {
          success: false,
          error: `${data.error_code}: ${data.description}`,
          chatId: destination
        };
      }
    } catch (err) {
      console.error(`[TELEGRAM NETWORK ERROR] to ${destination}:`, err.message);
      return {
        success: false,
        error: err.message,
        chatId: destination
      };
    }
  }

  async broadcastSignal(signal, targetChannels = null) {
    const isPreCatalyst = signal.channel_type || signal.hours_ahead_of_market || signal.lead_time_status;
    const formattedHtml = isPreCatalyst ? formatTelegramPreCatalystAlert(signal) : formatTelegramAlert(signal);

    const channels = (targetChannels && targetChannels.length > 0) ? targetChannels : [this.chatId || this.channelId];
    const results = [];

    for (const ch of channels) {
      const res = await this.sendTextMessage(ch, formattedHtml, 'HTML');
      results.push({ target: ch, ...res });
    }

    return {
      success: results.some(r => r.success),
      totalChannels: channels.length,
      formattedText: formattedHtml,
      results
    };
  }

  async sendTestMessage(targetChatId = null) {
    const target = targetChatId || this.chatId || this.channelId;
    const timeStr = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const testMsg = 
`⚡ <b>TEST NOTIFICATION: Institutional AI News Impact Engine</b>

• <b>Gateway Status:</b> 🟢 ONLINE (Sub-Second Telegram Channel Dispatch)
• <b>Channel:</b> <code>${this.channelId}</code>
• <b>Bot:</b> @${this.botUsername}
• <b>Time:</b> ${timeStr} IST

✅ <i>Your Telegram Channel is successfully linked and verified. Live high-conviction trade alerts and Pre-Catalyst Radar will broadcast here instantly.</i>`;

    return await this.sendTextMessage(target, testMsg, 'HTML');
  }
}

module.exports = TelegramNotificationService;
