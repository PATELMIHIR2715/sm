const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '.env') });
const nodemailer = require('nodemailer');
const { formatEmailHtml } = require('./notification_templates');

class EmailNotificationService {
  constructor() {
    this.transporter = null;
    this.status = 'UNINITIALIZED';
    this.defaultRecipients = (process.env.ALERT_EMAIL_RECIPIENTS || 'trader@institutional-edge.internal,analyst@alpha-fund.internal')
      .split(',')
      .map(e => e.trim());
    this.initTransporter();
  }

  initTransporter() {
    const host = process.env.SMTP_HOST;
    const port = parseInt(process.env.SMTP_PORT || '587', 10);
    const user = process.env.SMTP_USER;
    const pass = process.env.SMTP_PASS;

    if (host && user && pass) {
      this.transporter = nodemailer.createTransport({
        host,
        port,
        secure: port === 465,
        auth: { user, pass }
      });
      this.status = 'CONFIGURED_SMTP';
    } else {
      // Stream Transport for local development / testing without throwing error
      this.transporter = nodemailer.createTransport({
        jsonTransport: true
      });
      this.status = 'SIMULATION_MODE (Configure SMTP_HOST in .env for live dispatch)';
    }

    if (this.transporter.verify) {
      this.transporter.verify((error) => {
        if (error) {
          console.warn('[EMAIL WARNING] SMTP Verify note:', error.message);
          this.status = `AUTH_PENDING (${error.message})`;
        } else {
          this.status = 'READY_VERIFIED';
          console.log('[EMAIL SERVICE] SMTP Transport ready & verified.');
        }
      });
    }
  }

  async sendSignalEmail(signal, recipients = null) {
    const to = (recipients && recipients.length > 0) ? recipients : this.defaultRecipients;
    const sym = signal.symbol || 'STOCK';
    const dir = signal.predicted_direction || 'BULLISH';
    const htmlBody = formatEmailHtml(signal);

    const mailOptions = {
      from: process.env.SMTP_FROM || '"Institutional Stock Engine" <alerts@institutional-trading.internal>',
      to: to.join(', '),
      subject: `⚡ [${dir}] ${sym} High-Conviction Impact Alert — Targets & Sizing`,
      html: htmlBody
    };

    try {
      const info = await this.transporter.sendMail(mailOptions);
      console.log(`[EMAIL DISPATCH] Sent alert for ${sym} to ${to.join(', ')}`);
      return {
        success: true,
        messageId: info.messageId || 'LOCAL_SIMULATED_MSG_ID',
        recipients: to,
        dispatchedAt: new Date().toISOString()
      };
    } catch (err) {
      console.error(`[EMAIL ERROR] Failed sending alert for ${sym}:`, err.message);
      return {
        success: false,
        error: err.message,
        recipients: to
      };
    }
  }

  async sendTestEmail(targetEmail) {
    const to = targetEmail || this.defaultRecipients[0];
    const testSignal = {
      symbol: 'BHEL',
      predicted_direction: 'BULLISH',
      conviction_score_pct: 88.5,
      current_live_ltp_t0: 434.45,
      optimal_entry_price: 434.45,
      execution_order_type: 'ACCUMULATE_BEFORE_MOVE',
      catalyst_absorption_pct: 0.0,
      remaining_alpha_pct: 3.8,
      headline: 'TEST ALERT: BHEL declared lowest bidder (L1) for landmark INR 6,100 Crore NTPC Supercritical EPC contract',
      sector: 'Power & Capital Goods',
      predicted_tomorrows_price_range_t1: {
        predicted_price_bounds_inr: '₹442.20 – ₹451.80',
        expected_move_pct: '+1.8% to +4.0%'
      },
      recommended_stop_loss: '₹421.40 (-3.0%)',
      kelly_capital_allocation_inr: 18246,
      recommended_shares_quantity: 42
    };

    return this.sendSignalEmail(testSignal, [to]);
  }

  getStatus() {
    const rawUser = process.env.SMTP_USER || '';
    let userMasked = 'Not set';
    if (rawUser.includes('@')) {
      const [u, d] = rawUser.split('@');
      userMasked = `${u.slice(0, 3)}***@${d}`;
    } else if (rawUser) {
      userMasked = `${rawUser.slice(0, 3)}***`;
    }

    return {
      status: this.status,
      defaultRecipients: this.defaultRecipients,
      smtpHost: process.env.SMTP_HOST || 'Local JsonTransport',
      smtpUserMasked: userMasked,
      isPasswordConfigured: Boolean(process.env.SMTP_PASS && process.env.SMTP_PASS.length > 3)
    };
  }
}

module.exports = EmailNotificationService;
