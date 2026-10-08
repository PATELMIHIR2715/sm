const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const path = require('path');
const fs = require('fs');
const { formatWhatsAppAlert, formatWhatsAppPreCatalystAlert } = require('./notification_templates');

class WhatsAppNotificationService {
  constructor() {
    this.client = null;
    this.status = 'DISCONNECTED';
    this.qrCodeRaw = null;
    this.qrDataUrl = null;
    this.authenticatedUser = null;
    this.defaultRecipients = (process.env.ALERT_WHATSAPP_NUMBERS || '+919876543210')
      .split(',')
      .map(n => n.trim());
    this.isInitializing = false;
    this.initClient();
  }

  initClient() {
    if (this.isInitializing) return;
    this.isInitializing = true;
    this.status = 'INITIALIZING';

    try {
      this.client = new Client({
        authStrategy: new LocalAuth({
          dataPath: path.join(__dirname, '.wwebjs_auth')
        }),
        puppeteer: {
          headless: true,
          args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-extensions'
          ]
        }
      });

      this.client.on('qr', async (qr) => {
        this.status = 'QR_READY';
        this.qrCodeRaw = qr;
        try {
          this.qrDataUrl = await qrcode.toDataURL(qr, { margin: 2, width: 260 });
        } catch (e) {
          console.warn('[WHATSAPP QR ERROR]', e.message);
        }
        console.log('[WHATSAPP SERVICE] New QR code generated. Scan to authenticate via Dashboard or WhatsApp app.');
      });

      this.client.on('ready', () => {
        this.status = 'CONNECTED_READY';
        this.qrCodeRaw = null;
        this.qrDataUrl = null;
        try {
          this.authenticatedUser = this.client.info ? this.client.info.wid.user : 'Active Session';
        } catch (_) {
          this.authenticatedUser = 'Authenticated';
        }
        console.log(`[WHATSAPP SERVICE] Client is ready! Logged in as: ${this.authenticatedUser}`);
      });

      this.client.on('authenticated', () => {
        this.status = 'AUTHENTICATED';
        console.log('[WHATSAPP SERVICE] Session authenticated successfully.');
      });

      this.client.on('auth_failure', (msg) => {
        this.status = 'AUTH_FAILURE';
        console.error('[WHATSAPP AUTH FAILURE]', msg);
      });

      this.client.on('disconnected', (reason) => {
        this.status = 'DISCONNECTED';
        this.authenticatedUser = null;
        console.warn('[WHATSAPP DISCONNECTED]', reason);
      });

      this.client.initialize().catch((err) => {
        console.warn('[WHATSAPP INIT WARNING] Headless browser launch note:', err.message);
        this.status = 'AWAITING_BROWSER';
      });
    } catch (err) {
      console.error('[WHATSAPP CLIENT ERROR]', err.message);
      this.status = 'SETUP_ERROR';
    } finally {
      this.isInitializing = false;
    }
  }

  sanitizeChatId(numberOrId) {
    let clean = String(numberOrId).replace(/[^\d@a-z._]/gi, '');
    if (clean.includes('@c.us') || clean.includes('@g.us')) {
      return clean;
    }
    // Indian standard 10-digit number handling
    if (clean.length === 10) {
      clean = '91' + clean;
    }
    return `${clean}@c.us`;
  }

  async sendTextMessage(targetNumber, message) {
    const chatId = this.sanitizeChatId(targetNumber);

    if (this.status !== 'CONNECTED_READY') {
      console.log(`[WHATSAPP SIMULATION] Status is ${this.status}. Message queued/logged for ${chatId}:\n${message}\n`);
      return {
        success: true,
        simulated: true,
        status: this.status,
        chatId,
        messagePreview: message.substring(0, 100) + '...',
        note: 'WhatsApp Web client awaiting QR pairing. Scan QR code in Dashboard to enable live delivery.'
      };
    }

    try {
      const response = await this.client.sendMessage(chatId, message);
      console.log(`[WHATSAPP SENT] Delivered to ${chatId}`);
      return {
        success: true,
        simulated: false,
        messageId: response.id._serialized,
        chatId
      };
    } catch (err) {
      console.error(`[WHATSAPP SEND ERROR] to ${chatId}:`, err.message);
      return {
        success: false,
        error: err.message,
        chatId
      };
    }
  }

  async broadcastSignal(signal, targetNumbers = null) {
    const numbers = (targetNumbers && targetNumbers.length > 0) ? targetNumbers : this.defaultRecipients;
    const isPreCatalyst = signal.channel_type || signal.hours_ahead_of_market || signal.lead_time_status;
    const formattedText = isPreCatalyst ? formatWhatsAppPreCatalystAlert(signal) : formatWhatsAppAlert(signal);

    const results = [];
    for (const num of numbers) {
      const res = await this.sendTextMessage(num, formattedText);
      results.push({ number: num, ...res });
    }

    return {
      success: true,
      totalRecipients: numbers.length,
      formattedText,
      results
    };
  }

  async regenerateQrCode(forceClearSession = true) {
    console.log(`[WHATSAPP SERVICE] QR code regeneration triggered (forceClearSession=${forceClearSession})...`);
    this.status = 'AWAITING_QR';
    this.qrCodeRaw = null;
    this.qrDataUrl = null;
    this.authenticatedUser = null;

    if (this.client) {
      try {
        await this.client.destroy();
      } catch (err) {
        console.warn('[WHATSAPP DESTROY WARNING]', err.message);
      }
      this.client = null;
    }

    this.isInitializing = false;

    if (forceClearSession) {
      try {
        const authPath = path.join(__dirname, '.wwebjs_auth');
        if (fs.existsSync(authPath)) {
          fs.rmSync(authPath, { recursive: true, force: true });
          console.log('[WHATSAPP SERVICE] Expired session cache cleared from:', authPath);
        }
      } catch (err) {
        console.warn('[WHATSAPP CACHE CLEAR WARNING]', err.message);
      }
    }

    this.initClient();
    return {
      success: true,
      status: this.status,
      message: 'Fresh session initiated. Waiting for QR code generation from WhatsApp Web...'
    };
  }

  getStatus() {
    return {
      status: this.status,
      authenticatedUser: this.authenticatedUser,
      hasQrCode: Boolean(this.qrDataUrl),
      defaultRecipients: this.defaultRecipients
    };
  }

  getQrData() {
    return {
      status: this.status,
      qrDataUrl: this.qrDataUrl,
      qrCodeRaw: this.qrCodeRaw
    };
  }
}

module.exports = WhatsAppNotificationService;
