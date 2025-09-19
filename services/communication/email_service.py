"""
Email Service Module

Handles email communication using templates and SMTP.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import jinja2
from core.config.settings import settings
from core.config.logging_config import get_logger
from db.database import get_db
from models import Business, Owner
from sqlalchemy.orm import Session
from services import OwnerService, BusinessService, twilio_service
from db.database import get_db

logger = get_logger(__name__)


class EmailService:
    """Service for sending emails using templates"""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.email_pass = settings.EMAIL_PASS
        
        # Email templates
        self.templates = {
            'customer_data': """
            <!DOCTYPE html>
            <html lang=\"en\">
            <head>
                <meta charset=\"UTF-8\">
                <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
                <title>New Customer Contact</title>
                <style>
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: #6b46c1; padding: 24px; }
                    .template { max-width: 600px; margin: 0 auto; background: #f3e8ff; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.08); overflow: hidden; border: 1px solid #d8b4fe; }
                    .template-header { padding: 24px; color: #fff; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
                    .header-icon { font-size: 2rem; display: block; margin-bottom: 8px; }
                    h2 { font-size: 20px; font-weight: 700; }
                    .template-body { padding: 24px; }
                    .info-section { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 12px; padding: 16px; color: #fff; margin-bottom: 16px; }
                    .info-section h3 { font-size: 16px; margin-bottom: 12px; }
                    .info-list { list-style: none; }
                    .info-list li { background: rgba(255,255,255,0.15); padding: 10px 12px; border-radius: 10px; margin-bottom: 10px; }
                    .info-list strong { font-weight: 600; margin-right: 6px; }
                    .info-list a { color: #ffffff; text-decoration: none; }
                    .reason-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; padding: 14px; border-radius: 12px; margin: 14px 0; border-left: 4px solid #ffffff; }
                    .tag { display: inline-block; padding: 6px 12px; border-radius: 999px; font-weight: 600; font-size: 12px; }
                    .contact-tag { background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%); color: #2c3e50; }
                    .urgency-high { background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); color: #fff; }
                    .urgency-normal { background: linear-gradient(135deg, #00b894 0%, #00a085 100%); color: #fff; }
                    .notes-section { background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); color: #8b4513; padding: 14px; border-radius: 12px; margin: 14px 0; border: 2px dashed rgba(139, 69, 19, 0.3); }
                    .footer { background: #ede9fe; color: #4a5568; padding: 16px 20px; text-align: center; font-style: italic; border-top: 1px solid #d8b4fe; }
                </style>
            </head>
            <body>
                <div class=\"template\">
                    <div class=\"template-header\">
                        <span class=\"header-icon\">🎯</span>
                        <h2>New Customer Contact</h2>
                    </div>
                    <div class=\"template-body\">
                        <div class=\"info-section\">
                            <h3>Customer Information</h3>
                            <ul class=\"info-list\">
                                <li><strong>Name:</strong> {{ client_name }}</li>
                                <li><strong>Phone:</strong> <a href=\"tel:{{ phone_number }}\">{{ phone_number }}</a></li>
                                {% if address %}
                                <li><strong>Address:</strong> {{ address }}</li>
                                {% endif %}
                            </ul>
                        </div>
                        <div class=\"reason-box\">
                            <strong>Reason for calling:</strong> {{ reason_calling }}
                        </div>
                        <p><strong>Preferred contact:</strong> <span class=\"tag contact-tag\">{{ preferred_contact_method }}</span></p>
                        {% if urgency %}
                        <p><strong>Urgency:</strong> 
                            <span class=\"tag {% if urgency in ['high', 'urgent'] %}urgency-high{% else %}urgency-normal{% endif %}\">{{ urgency.upper() }}</span>
                        </p>
                        {% endif %}
                        {% if additional_notes %}
                        <div class=\"notes-section\">
                            <strong>Notes:</strong> {{ additional_notes }}
                        </div>
                        {% endif %}
                    </div>
                    <div class=\"footer\">
                        <em>This customer data has been automatically validated using the CustomerCall schema.</em>
                    </div>
                </div>
            </body>
            </html>
            """,
            'meeting_scheduled': """
            <!DOCTYPE html>
            <html lang=\"en\">
            <head>
                <meta charset=\"UTF-8\">
                <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
                <title>Meeting Scheduled</title>
                <style>
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: #6b46c1; padding: 24px; }
                    .template { max-width: 600px; margin: 0 auto; background: #f3e8ff; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.08); overflow: hidden; border: 1px solid #d8b4fe; }
                    .template-header { padding: 24px; color: #fff; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
                    .header-icon { font-size: 2rem; display: block; margin-bottom: 8px; }
                    h2 { font-size: 20px; font-weight: 700; }
                    .template-body { padding: 24px; }
                    .meeting-details { background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); color: #2c3e50; border-radius: 12px; padding: 16px; margin-bottom: 16px; }
                    .info-list { list-style: none; }
                    .info-list li { background: #f7f9fc; padding: 10px 12px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #eef2f7; }
                    .info-list strong { font-weight: 600; margin-right: 6px; }
                    .alert-box { background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); color: #d63031; padding: 14px; border-radius: 12px; margin: 14px 0; border: 2px solid #d63031; text-align: center; font-weight: 600; }
                    .footer { background: #ede9fe; color: #4a5568; padding: 16px 20px; text-align: center; font-style: italic; border-top: 1px solid #d8b4fe; }
                </style>
            </head>
            <body>
                <div class=\"template\">
                    <div class=\"template-header\">
                        <span class=\"header-icon\">📅</span>
                        <h2>Meeting Scheduled</h2>
                    </div>
                    <div class=\"template-body\">
                        <div class=\"meeting-details\">
                            <h3>Meeting Details</h3>
                            <ul class=\"info-list\">
                                <li><strong>Client:</strong> {{ client_name }}</li>
                                <li><strong>Date:</strong> {{ preferred_date }}</li>
                                <li><strong>Address:</strong> {{ address }}</li>
                                <li><strong>Reach Out Method:</strong> {{ meeting_type }}</li>
                                <li>{% if notes %}<strong>Notes:</strong> {{ notes }}{% endif %}</li>
                            </ul>
                        </div>
                        <div class=\"alert-box\">
                            <strong>⚠️ Important:</strong> Please confirm this meeting with the client before the scheduled time.
                        </div>
                    </div>
                    <div class=\"footer\">
                        <em>This is an automated message from your voice agent system.</em>
                    </div>
                </div>
            </body>
            </html>
            """,
            'high_priority': """
            <!DOCTYPE html>
            <html lang=\"en\">
            <head>
                <meta charset=\"UTF-8\">
                <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
                <title>High Priority Customer Contact</title>
                <style>
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: #6b46c1; padding: 24px; }
                    .template { max-width: 600px; margin: 0 auto; background: #f3e8ff; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.08); overflow: hidden; border: 1px solid #d8b4fe; }
                    .template-header { padding: 24px; color: #fff; background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
                    .header-icon { font-size: 2rem; display: block; margin-bottom: 8px; }
                    h2 { font-size: 20px; font-weight: 700; }
                    .template-body { padding: 24px; }
                    .priority-urgency { background: linear-gradient(135deg, #ff0844 0%, #ffb199 100%); color: #fff; padding: 12px; border-radius: 10px; text-align: center; margin-bottom: 16px; font-size: 14px; font-weight: 700; }
                    .info-section { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 12px; padding: 16px; color: #fff; margin-bottom: 16px; }
                    .info-section h3 { font-size: 16px; margin-bottom: 12px; }
                    .info-list { list-style: none; }
                    .info-list li { background: rgba(255,255,255,0.15); padding: 10px 12px; border-radius: 10px; margin-bottom: 10px; }
                    .info-list a { color: #ffffff; text-decoration: none; }
                    .reason-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; padding: 14px; border-radius: 12px; margin: 14px 0; border-left: 4px solid #ffffff; }
                    .priority-alert { background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%); color: #fff; padding: 16px; border-radius: 12px; text-align: center; font-weight: 700; margin-top: 14px; }
                    .footer { background: #ede9fe; color: #4a5568; padding: 16px 20px; text-align: center; font-style: italic; border-top: 1px solid #d8b4fe; }
                </style>
            </head>
            <body>
                <div class=\"template\">
                    <div class=\"template-header\">
                        <span class=\"header-icon\">🚨</span>
                        <h2>HIGH PRIORITY CUSTOMER CONTACT</h2>
                    </div>
                    <div class=\"template-body\">
                        <div class=\"priority-urgency\">Urgency Level: {{ urgency }}</div>
                        <div class=\"info-section\">
                            <h3>Validated Customer Information</h3>
                            <ul class=\"info-list\">
                                <li><strong>Name:</strong> {{ client_name }}</li>
                                <li><strong>Phone:</strong> <a href=\"tel:{{ phone_number }}\">{{ phone_number }}</a></li>
                                <li><strong>Preferred Contact:</strong> {{ preferred_contact_method }}</li>
                            </ul>
                        </div>
                        <div class=\"reason-box\">
                            <strong>Reason:</strong> {{ reason_calling }}
                        </div>
                        {% if additional_notes %}
                        <div class=\"info-section\" style=\"background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); color: #8b4513;\">
                            <strong>Notes:</strong> {{ additional_notes }}
                        </div>
                        {% endif %}
                        <div class=\"priority-alert\">⚡ Action Required: This customer requires immediate attention!</div>
                    </div>
                    <div class=\"footer\">
                        <em>This is an automated HIGH PRIORITY alert from your voice agent system.</em>
                    </div>
                </div>
            </body>
            </html>
            """
        }
        
        self.template_env = jinja2.Environment(loader=jinja2.DictLoader(self.templates))
    
    def send_email(self, subject: str, template_name: str, data: Dict[Any, Any]) -> bool:
        """Send email using template"""
        db = next(get_db())
        try:
            call_sid = data.get('call_sid')
            if not all([settings.EMAIL_PASS, call_sid]):
                logger.warning("Email credentials not configured")
                return False
            call = twilio_service.get_call(call_sid)
            forwarded_from = call.forwarded_from if call.forwarded_from != call.to else settings.FORWARDED_FROM
            business = BusinessService.get_business(db, forwarded_from)
            assert business, "Business not found"
            template = self.template_env.get_template(template_name)
            html_content = template.render(**data)
            
            msg = MIMEMultipart('alternative')
            msg['From'] = settings.BUSINESS_EMAIL
            msg['To'] = business.email
            msg['Subject'] = subject
            
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(settings.BUSINESS_EMAIL, settings.EMAIL_PASS)
                server.send_message(msg)
            
            logger.info(f"✅ Email sent: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            return False
    
    def is_configured(self) -> bool:
        """Check if email service is properly configured"""
        return all([settings.BUSINESS_EMAIL, settings.EMAIL_PASS])
