/**
 * Clean & Minimalist Institutional Notification Templates for WhatsApp and Email
 * Focused strictly on core trader essentials: Symbol, Action, Current Price, T1, T2, When to Wait for T2, Stop-Loss, and Reason.
 */

function cleanReason(text) {
  if (!text) return 'Material corporate catalyst reported on exchange.';
  // Strip exchange scrip code noise like " - 532540 - " or "500123 - "
  let cleaned = text.replace(/\s*-\s*\d{5,6}\s*-\s*/g, ' - ');
  cleaned = cleaned.replace(/\s{2,}/g, ' ').trim();
  if (cleaned.length > 200) {
    cleaned = cleaned.slice(0, 197) + '...';
  }
  return cleaned;
}

function formatWhatsAppAlert(signal) {
  const sym = signal.symbol || 'STOCK';
  const dir = signal.predicted_direction || 'BULLISH';
  const isBull = dir.toUpperCase() === 'BULLISH';
  const actionText = isBull ? '🟢 BUY' : '🔴 SELL';
  const actionTitle = isBull ? 'BUY' : 'SELL';
  
  const ltp = Number(signal.current_live_ltp_t0 || signal.current_base_price_inr || signal.ltp || 0);
  const formattedLtp = ltp > 0 ? `₹${ltp.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : 'N/A';
  
  const tt = signal.two_tier_targets || {};
  const t1Safe = tt.t1_safe || signal.t1_safe_target;
  const t2Runner = tt.t2_runner || signal.t2_runner_target;

  let t1PriceStr = 'N/A';
  let t1PctStr = '';
  let t2PriceStr = 'N/A';
  let t2PctStr = '';

  if (t1Safe && t1Safe.price) {
    t1PriceStr = `₹${Number(t1Safe.price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    t1PctStr = ` (${t1Safe.percentage})`;
  } else if (signal.t1_target && signal.t1_target.price_target_range_inr) {
    t1PriceStr = signal.t1_target.price_target_range_inr;
    t1PctStr = signal.t1_target.percentage_range ? ` (${signal.t1_target.percentage_range})` : '';
  }

  if (t2Runner && t2Runner.price) {
    t2PriceStr = `₹${Number(t2Runner.price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    t2PctStr = ` (${t2Runner.percentage})`;
  } else {
    t2PriceStr = t1PriceStr;
  }

  const sl = signal.recommended_stop_loss || (ltp > 0 ? `₹${(isBull ? ltp * 0.97 : ltp * 1.03).toFixed(2)} (${isBull ? '-3.0%' : '+3.0%'})` : 'N/A');
  
  const whenToWaitForT2 = isBull
    ? `Hold remaining 30% only if price sustains above T1 (${t1PriceStr}) with strong volume. Move Stop-Loss to entry price (${formattedLtp}).`
    : `Hold remaining 30% only if selling momentum continues below T1 (${t1PriceStr}). Trail Stop-Loss to entry price (${formattedLtp}).`;

  const reason = cleanReason(signal.headline);
  const engineVer = signal.model_version || signal.engine_version || 'v3.0';
  const isAfterHours = signal.market_session === 'AFTER_HOURS_CLOSED' || signal.is_after_hours;
  const timingNote = isAfterHours ? '⏰ *Market Closed* — Tradable Tomorrow 09:15 AM\n' : '';
  const circuitNote = signal.circuit_warning ? `⚠️ *${signal.circuit_warning}*\n` : '';

  return (
`${timingNote}${circuitNote}🎯 *${sym} — ${actionTitle} ALERT*

• *Action:* ${actionText}
• *Current Price:* ${formattedLtp}
• *Stop-Loss:* ${sl}

🎯 *Targets:*
• *T1 (Safe Exit):* ${t1PriceStr}${t1PctStr} — [Book 70% Profit]
• *T2 (Runner):* ${t2PriceStr}${t2PctStr}

💡 *When to wait for T2:*
${whenToWaitForT2}

📌 *Reason:*
${reason}

⏱️ ${new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })} IST • Engine ${engineVer}`
  );
}

function formatWhatsAppPreCatalystAlert(item) {
  const sym = item.symbol || 'STOCK';
  const ltp = Number(item.current_ltp || item.current_base_price_inr || 0);
  const formattedLtp = ltp > 0 ? `₹${ltp.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : (item.pre_catalyst_entry_corridor || 'N/A');
  const target = item.target_upon_announcement || 'N/A';
  const sl = item.stop_loss || 'N/A';
  const reason = cleanReason(item.upstream_headline || item.headline);

  return (
`⚡ *EARLY RADAR: ${sym} — BUY ALERT*

• *Action:* 🟢 BUY (Before News Repricing)
• *Current Price:* ${formattedLtp}
• *Stop-Loss:* ${sl}

🎯 *Target:* ${target}

📌 *Reason:*
${reason}

⏱️ ${new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })} IST`
  );
}

function formatEmailHtml(signal) {
  const sym = signal.symbol || 'STOCK';
  const dir = signal.predicted_direction || 'BULLISH';
  const isBull = dir.toUpperCase() === 'BULLISH';
  const actionText = isBull ? 'BUY' : 'SELL';
  const actionColor = isBull ? '#10b981' : '#ef4444';
  const ltp = Number(signal.current_live_ltp_t0 || signal.current_base_price_inr || signal.ltp || 0);
  const formattedLtp = ltp > 0 ? `₹${ltp.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : 'N/A';
  
  const tt = signal.two_tier_targets || {};
  const t1Safe = tt.t1_safe || signal.t1_safe_target;
  const t2Runner = tt.t2_runner || signal.t2_runner_target;

  let t1PriceStr = 'N/A';
  let t1PctStr = '';
  let t2PriceStr = 'N/A';
  let t2PctStr = '';

  if (t1Safe && t1Safe.price) {
    t1PriceStr = `₹${Number(t1Safe.price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    t1PctStr = ` (${t1Safe.percentage})`;
  } else if (signal.t1_target && signal.t1_target.price_target_range_inr) {
    t1PriceStr = signal.t1_target.price_target_range_inr;
    t1PctStr = signal.t1_target.percentage_range ? ` (${signal.t1_target.percentage_range})` : '';
  }

  if (t2Runner && t2Runner.price) {
    t2PriceStr = `₹${Number(t2Runner.price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    t2PctStr = ` (${t2Runner.percentage})`;
  } else {
    t2PriceStr = t1PriceStr;
  }

  const sl = signal.recommended_stop_loss || 'N/A';
  const whenToWaitForT2 = isBull
    ? `Hold remaining 30% only if price sustains above T1 (${t1PriceStr}) with strong volume. Move Stop-Loss to entry price (${formattedLtp}).`
    : `Hold remaining 30% only if selling momentum continues below T1 (${t1PriceStr}). Trail Stop-Loss to entry price (${formattedLtp}).`;

  const reason = cleanReason(signal.headline);
  const engineVer = signal.model_version || signal.engine_version || 'v3.0';

  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
    .container { max-width: 520px; margin: 0 auto; background-color: #1e293b; border-radius: 12px; overflow: hidden; border: 1px solid #334155; }
    .header { padding: 18px 24px; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; }
    .title { font-size: 20px; font-weight: bold; margin: 0; color: #ffffff; }
    .badge { display: inline-block; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 13px; color: #ffffff; background-color: ${actionColor}; }
    .content { padding: 20px 24px; }
    .row { display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 14px; }
    .label { color: #94a3b8; }
    .val { font-weight: bold; color: #ffffff; }
    .targets-box { background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 14px; margin: 16px 0; }
    .target-line { margin-bottom: 8px; font-size: 14px; }
    .target-line:last-child { margin-bottom: 0; }
    .guidance-box { background: rgba(56, 189, 248, 0.08); border-left: 3px solid #38bdf8; padding: 10px 14px; border-radius: 0 6px 6px 0; font-size: 13px; color: #e2e8f0; margin-bottom: 16px; line-height: 1.4; }
    .reason-box { background: #0f172a; border-radius: 6px; padding: 12px 14px; font-size: 13px; color: #cbd5e1; line-height: 1.5; }
    .footer { padding: 12px 24px; background: #0f172a; border-top: 1px solid #334155; font-size: 11px; color: #64748b; text-align: center; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h2 class="title">🎯 ${sym}</h2>
      <span class="badge">${actionText}</span>
    </div>

    <div class="content">
      <div class="row">
        <span class="label">Current Price:</span>
        <span class="val">${formattedLtp}</span>
      </div>
      <div class="row">
        <span class="label">Stop-Loss:</span>
        <span class="val" style="color: #ef4444;">${sl}</span>
      </div>

      <div class="targets-box">
        <div class="target-line">
          <strong style="color: #10b981;">• T1 (Safe Exit):</strong> ${t1PriceStr}${t1PctStr} — <span style="font-size: 12px; color: #94a3b8;">Book 70% Profit</span>
        </div>
        <div class="target-line">
          <strong style="color: #38bdf8;">• T2 (Runner):</strong> ${t2PriceStr}${t2PctStr}
        </div>
      </div>

      <div class="guidance-box">
        <strong style="color: #38bdf8;">💡 When to wait for T2:</strong><br/>
        ${whenToWaitForT2}
      </div>

      <div class="reason-box">
        <strong style="color: #ffffff;">📌 Reason:</strong><br/>
        ${reason}
      </div>
    </div>

    <div class="footer">
      Dispatched at ${new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })} IST • Engine ${engineVer}
    </div>
  </div>
</body>
</html>
  `;
}

function escapeTelegramHtml(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function formatTelegramAlert(signal) {
  const sym = escapeTelegramHtml(signal.symbol || 'STOCK');
  const dir = signal.predicted_direction || 'BULLISH';
  const isBull = dir.toUpperCase() === 'BULLISH';
  const actionText = isBull ? '🟢 <b>BUY</b>' : '🔴 <b>SELL</b>';
  const actionTitle = isBull ? 'BUY' : 'SELL';
  
  const ltp = Number(signal.current_live_ltp_t0 || signal.current_base_price_inr || signal.ltp || 0);
  const formattedLtp = ltp > 0 ? `₹${ltp.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : 'N/A';
  
  const tt = signal.two_tier_targets || {};
  const t1Safe = tt.t1_safe || signal.t1_safe_target;
  const t2Runner = tt.t2_runner || signal.t2_runner_target;

  let t1PriceStr = 'N/A';
  let t1PctStr = '';
  let t2PriceStr = 'N/A';
  let t2PctStr = '';

  if (t1Safe && t1Safe.price) {
    t1PriceStr = `₹${Number(t1Safe.price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    t1PctStr = ` (${escapeTelegramHtml(t1Safe.percentage)})`;
  } else if (signal.t1_target && signal.t1_target.price_target_range_inr) {
    t1PriceStr = escapeTelegramHtml(signal.t1_target.price_target_range_inr);
    t1PctStr = signal.t1_target.percentage_range ? ` (${escapeTelegramHtml(signal.t1_target.percentage_range)})` : '';
  }

  if (t2Runner && t2Runner.price) {
    t2PriceStr = `₹${Number(t2Runner.price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    t2PctStr = ` (${escapeTelegramHtml(t2Runner.percentage)})`;
  } else {
    t2PriceStr = t1PriceStr;
  }

  const sl = escapeTelegramHtml(signal.recommended_stop_loss || (ltp > 0 ? `₹${(isBull ? ltp * 0.97 : ltp * 1.03).toFixed(2)} (${isBull ? '-3.0%' : '+3.0%'})` : 'N/A'));
  
  const whenToWaitForT2 = isBull
    ? `Hold remaining 30% only if price sustains above T1 (<b>${t1PriceStr}</b>) with strong volume. Move Stop-Loss to entry price (<b>${formattedLtp}</b>).`
    : `Hold remaining 30% only if selling momentum continues below T1 (<b>${t1PriceStr}</b>). Trail Stop-Loss to entry price (<b>${formattedLtp}</b>).`;

  const reason = escapeTelegramHtml(cleanReason(signal.headline));
  const engineVer = escapeTelegramHtml(signal.model_version || signal.engine_version || 'v3.0');
  const isAfterHours = signal.market_session === 'AFTER_HOURS_CLOSED' || signal.is_after_hours;
  const timingNote = isAfterHours ? '⏰ <b>Market Closed</b> — Tradable Tomorrow 09:15 AM\n' : '';
  const circuitNote = signal.circuit_warning ? `⚠️ <b>${escapeTelegramHtml(signal.circuit_warning)}</b>\n` : '';

  return (
`${timingNote}${circuitNote}🎯 <b>${sym} — ${actionTitle} ALERT</b>

• <b>Action:</b> ${actionText}
• <b>Current Price:</b> <code>${formattedLtp}</code>
• <b>Stop-Loss:</b> <code>${sl}</code>

🎯 <b>Targets:</b>
• <b>T1 (Safe Exit):</b> <code>${t1PriceStr}</code>${t1PctStr} — [Book 70% Profit]
• <b>T2 (Runner):</b> <code>${t2PriceStr}</code>${t2PctStr}

💡 <b>When to wait for T2:</b>
${whenToWaitForT2}

📌 <b>Reason:</b>
${reason}

⏱️ ${new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })} IST • Engine ${engineVer}`
  );
}

function formatTelegramPreCatalystAlert(item) {
  const sym = escapeTelegramHtml(item.symbol || 'STOCK');
  const ltp = Number(item.current_ltp || item.current_base_price_inr || 0);
  const formattedLtp = ltp > 0 ? `₹${ltp.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : escapeTelegramHtml(item.pre_catalyst_entry_corridor || 'N/A');
  const target = escapeTelegramHtml(item.target_upon_announcement || 'N/A');
  const sl = escapeTelegramHtml(item.stop_loss || 'N/A');
  const reason = escapeTelegramHtml(cleanReason(item.upstream_headline || item.headline));

  return (
`⚡ <b>EARLY RADAR: ${sym} — BUY ALERT</b>

• <b>Action:</b> 🟢 <b>BUY</b> (Before News Repricing)
• <b>Current Price:</b> <code>${formattedLtp}</code>
• <b>Stop-Loss:</b> <code>${sl}</code>

🎯 <b>Target:</b> <code>${target}</code>

📌 <b>Reason:</b>
${reason}

⏱️ ${new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })} IST`
  );
}

module.exports = {
  cleanReason,
  formatWhatsAppAlert,
  formatWhatsAppPreCatalystAlert,
  formatEmailHtml,
  formatTelegramAlert,
  formatTelegramPreCatalystAlert,
  escapeTelegramHtml
};
