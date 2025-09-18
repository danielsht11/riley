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
            <h2>🎯 New Customer Contact</h2>
            <p><strong>Time:</strong> {{ timestamp }}</p>
            <p><strong>Stream ID:</strong> {{ stream_id }}</p>
            <p><strong>Validation:</strong> <span style="color: green;">✅ VALIDATED</span></p>
            
            <h3>Customer Information:</h3>
            <ul>
            <li><strong>Name:</strong> {{ full_name }}</li>
            <li><strong>Phone:</strong> <a href="tel:{{ phone_number }}">{{ phone_number }}</a></li>
            {% if email %}<li><strong>Email:</strong> <a href="mailto:{{ email }}">{{ email }}</a></li>{% endif %}
            {% if company %}<li><strong>Company:</strong> {{ company }}</li>{% endif %}
            <li><strong>Address:</strong> {{ address }}</li>
            </ul>
            
            <h3>Contact Details:</h3>
            <p><strong>Reason for calling:</strong> {{ reason_calling }}</p>
            <p><strong>Preferred contact:</strong> <span style="background: #e3f2fd; padding: 2px 6px; border-radius: 4px;">{{ preferred_contact_method }}</span></p>
            {% if urgency %}<p><strong>Urgency:</strong> <span style="color: {% if urgency in ['high', 'urgent'] %}red{% else %}green{% endif %};">{{ urgency.upper() }}</span></p>{% endif %}
            {% if additional_notes %}<p><strong>Notes:</strong> {{ additional_notes }}</p>{% endif %}
            
            <hr>
            <p><em>This customer data has been automatically validated using the CustomerCall schema.</em></p>
            """,
            
            'customer_data_invalid': """
            <h2>⚠️ New Customer Contact - VALIDATION FAILED</h2>
            <p><strong>Time:</strong> {{ timestamp }}</p>
            <p><strong>Stream ID:</strong> {{ stream_id }}</p>
            <p><strong>Validation:</strong> <span style="color: red;">❌ VALIDATION FAILED</span></p>
            <p><strong>Error:</strong> <code>{{ validation_error }}</code></p>
            
            <h3>Raw Customer Data (Needs Manual Review):</h3>
            <ul>
            {% if full_name %}<li><strong>Name:</strong> {{ full_name }}</li>{% endif %}
            {% if phone_number %}<li><strong>Phone:</strong> {{ phone_number }} <em>(may be invalid)</em></li>{% endif %}
            {% if email %}<li><strong>Email:</strong> {{ email }}</li>{% endif %}
            {% if company %}<li><strong>Company:</strong> {{ company }}</li>{% endif %}
            {% if address %}<li><strong>Address:</strong> {{ address }}</li>{% endif %}
            {% if reason_calling %}<li><strong>Reason:</strong> {{ reason_calling }}</li>{% endif %}
            {% if preferred_contact %}<li><strong>Preferred Contact:</strong> {{ preferred_contact }} <em>(may be invalid)</em></li>{% endif %}
            {% if notes %}<li><strong>Notes:</strong> {{ notes }}</li>{% endif %}
            </ul>
            
            <p><strong>⚠️ Action Required:</strong> Please manually validate and correct this customer information before follow-up.</p>
            
            <hr>
            <p><em>This is an automated validation failure alert from your voice agent system.</em></p>
            """,
            
            'meeting_scheduled': """
            <h2>📅 Meeting Scheduled</h2>
            <p><strong>Time:</strong> {{ timestamp }}</p>
            
            <h3>Meeting Details:</h3>
            <ul>
            <li><strong>Client:</strong> {{ client_name }}</li>
            <li><strong>Date:</strong> {{ preferred_date }}</li>
            <li><strong>Time:</strong> {{ preferred_time }}</li>
            <li><strong>Address:</strong> {{ address }}</li>
            <li><strong>Reach Out Method:</strong> {{ meeting_type }}</li>
            {% if notes %}<li><strong>Notes:</strong> {{ notes }}</li>{% endif %}
            </ul>
            
            <p><strong>⚠️ Important:</strong> Please confirm this meeting with the client before the scheduled time.</p>
            
            <hr>
            <p><em>This is an automated message from your voice agent system.</em></p>
            """,
            
            'high_priority': """
            <h2>🚨 HIGH PRIORITY CUSTOMER CONTACT</h2>
            <p><strong>Time:</strong> {{ timestamp }}</p>
            <p><strong>Urgency Level:</strong> <span style="color: red; font-weight: bold;">{{ urgency }}</span></p>
            
            <h3>Validated Customer Information:</h3>
            <ul>
            <li><strong>Name:</strong> {{ full_name }}</li>
            <li><strong>Phone:</strong> <a href="tel:{{ phone_number }}">{{ phone_number }}</a></li>
            {% if email %}<li><strong>Email:</strong> <a href="mailto:{{ email }}">{{ email }}</a></li>{% endif %}
            <li><strong>Preferred Contact:</strong> {{ preferred_contact_method }}</li>
            </ul>
            
            <p><strong>Reason:</strong> {{ reason_calling }}</p>
            {% if additional_notes %}<p><strong>Notes:</strong> {{ additional_notes }}</p>{% endif %}
            
            <p><strong>⚡ Action Required:</strong> This customer requires immediate attention!</p>
            
            <hr>
            <p><em>This is an automated HIGH PRIORITY alert from your voice agent system.</em></p>
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
