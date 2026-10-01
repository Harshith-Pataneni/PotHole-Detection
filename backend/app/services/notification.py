"""
Modular Notification Service
============================
Dispatches administrative notifications when a pothole report is verified.
Supports:
- Console logger (Safe dev default, logs complete transactional email body)
- SMTP (Standard transactional mail)
- Resend API (HTTP-based transactional service)
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
from app.config import settings
from app.core.logging import logger


class NotificationService:
    def __init__(self):
        self.provider = settings.EMAIL_PROVIDER.lower()

    async def send_pothole_alert(self, report_data: dict) -> bool:
        """
        Sends email notification to the municipal administrator.
        Data dictionary contains:
        - public_id
        - latitude
        - longitude
        - address_text
        - user_priority
        - model_confidence
        - estimated_severity
        - created_at
        """
        public_id = report_data.get("public_id", "UNKNOWN")
        coords = f"{report_data.get('latitude', 0.0):.5f}, {report_data.get('longitude', 0.0):.5f}"
        address = report_data.get("address_text") or "Coordinates Provided"
        user_priority = report_data.get("user_priority", "MEDIUM")
        confidence_pct = f"{report_data.get('model_confidence', 0.0) * 100:.1f}%"
        severity = report_data.get("estimated_severity", "MEDIUM")
        timestamp = report_data.get("created_at")
        admin_link = f"{settings.FRONTEND_URL}/admin/reports/{public_id}"

        subject = f"[CIVIC ALERT] New Pothole Report: {public_id} ({severity} Severity)"

        body_text = f"""
==================================================
CIVIC ROAD DEFECT REPORT: {public_id}
==================================================
A new verified road defect has been logged by the civic pothole reporting platform.

DETAILS:
- Report ID:           {public_id}
- Location:            {address}
- Coordinates:         {coords}
- Citizen Priority:    {user_priority}
- AI Confidence:       {confidence_pct}
- Estimated Severity:  {severity}
- Timestamp:           {timestamp}

View and manage this report in the Admin Dashboard:
{admin_link}
==================================================
"""

        body_html = f"""
<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1e293b; background: #f8fafc; padding: 20px; }}
    .card {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; }}
    .header {{ background: #0f172a; color: #f8fafc; padding: 24px; text-align: left; }}
    .header h1 {{ margin: 0; font-size: 20px; }}
    .content {{ padding: 24px; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 13px; }}
    .badge-critical {{ background: #fee2e2; color: #991b1b; }}
    .badge-high {{ background: #ffedd5; color: #9a3412; }}
    .badge-medium {{ background: #fef3c7; color: #92400e; }}
    .badge-low {{ background: #f1f5f9; color: #475569; }}
    .row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f1f5f9; font-size: 14px; }}
    .label {{ color: #64748b; font-weight: 500; }}
    .value {{ font-weight: 600; color: #0f172a; }}
    .btn {{ display: block; text-align: center; background: #2563eb; color: #ffffff; text-decoration: none; padding: 12px; border-radius: 6px; font-weight: 600; margin-top: 20px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <h1>New Road Defect Verified</h1>
      <p style="margin: 4px 0 0; color: #94a3b8; font-size: 14px;">Report Reference: {public_id}</p>
    </div>
    <div class="content">
      <div class="row"><span class="label">Location</span><span class="value">{address}</span></div>
      <div class="row"><span class="label">GPS Coordinates</span><span class="value">{coords}</span></div>
      <div class="row"><span class="label">Citizen Reported Priority</span><span class="value">{user_priority}</span></div>
      <div class="row"><span class="label">Model Confidence</span><span class="value">{confidence_pct}</span></div>
      <div class="row"><span class="label">Estimated Severity</span><span class="value">{severity}</span></div>
      <div class="row"><span class="label">Logged At</span><span class="value">{timestamp}</span></div>
      <a href="{admin_link}" class="btn">Open Report in Admin Portal &rarr;</a>
    </div>
  </div>
</body>
</html>
"""

        # Dispatch based on provider
        if self.provider == "resend" and settings.RESEND_API_KEY:
            return await self._send_resend(subject, body_html)
        elif self.provider == "smtp" and settings.SMTP_HOST:
            return await self._send_smtp(subject, body_text, body_html)
        else:
            # Console logger fallback (safe development mode)
            logger.info(f"[EMAIL NOTIFICATION DISPATCHED] (Provider: CONSOLE)")
            logger.info(f"Recipient: {settings.ADMIN_ALERT_EMAIL} | Subject: {subject}")
            logger.info(body_text.strip())
            return True

    async def _send_resend(self, subject: str, html: str) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": settings.EMAIL_FROM,
                        "to": [settings.ADMIN_ALERT_EMAIL],
                        "subject": subject,
                        "html": html
                    },
                    timeout=10.0
                )
                if resp.status_code in [200, 201]:
                    logger.info("Resend notification dispatched successfully.")
                    return True
                logger.error(f"Resend notification failed with status {resp.status_code}: {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Exception sending Resend notification: {e}")
            return False

    async def _send_smtp(self, subject: str, text: str, html: str) -> bool:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.EMAIL_FROM
            msg["To"] = settings.ADMIN_ALERT_EMAIL

            msg.attach(MIMEText(text, "plain"))
            msg.attach(MIMEText(html, "html"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10.0) as server:
                server.starttls()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(settings.EMAIL_FROM, [settings.ADMIN_ALERT_EMAIL], msg.as_string())

            logger.info("SMTP email alert dispatched successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to dispatch SMTP email alert: {e}")
            return False


notification_service = NotificationService()
