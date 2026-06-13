import base64
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from googleapiclient.discovery import build

def create_email_draft(
    to: list,
    subject: str,
    body: str = None,
    html_body: str = None,
    text_body: str = None,
    creds = None
) -> dict:
    """
    Creates a draft in Gmail.
    Supports standard body (plain text or html auto-detected) or explicit html_body and text_body.
    """
    service = build('gmail', 'v1', credentials=creds)
    
    # Create multipart MIME message
    message = MIMEMultipart('alternative')
    message['Subject'] = subject
    
    if isinstance(to, list):
        message['To'] = ", ".join(to)
    else:
        message['To'] = str(to)
        
    # Determine HTML and plaintext contents
    final_html = html_body
    final_text = text_body
    
    if not final_html and not final_text:
        # Fallback to single body parameter
        content = body or ""
        is_html = "<div" in content or "<html" in content or "<p" in content
        if is_html:
            final_html = content
            # Clean HTML tags for basic plaintext fallback
            temp = content.replace("<br>", "\n").replace("<p>", "\n").replace("</div>", "\n")
            final_text = re.sub(r'<[^>]*>', '', temp)
        else:
            final_text = content
            
    # Attach plaintext fallback
    if final_text:
        message.attach(MIMEText(final_text, 'plain', 'utf-8'))
        
    # Attach HTML content
    if final_html:
        message.attach(MIMEText(final_html, 'html', 'utf-8'))
        
    # Encode message to base64url
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    
    draft_body = {
        'message': {
            'raw': raw_message
        }
    }
    
    draft = service.users().drafts().create(userId='me', body=draft_body).execute()
    return draft
