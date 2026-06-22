import requests
import imaplib
import email
import re
import time
from email.header import decode_header

from services.email_service import message_matches_filters

# Microsoft OAuth Endpoint
TENANT_ID = 'common'
TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

def get_access_token(refresh_token, client_id):
    """
    Get an access token from a refresh token.
    """
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
        # Some client IDs may not require an explicit scope.
        # If this fails, try adding scope='https://outlook.office.com/IMAP.AccessAsUser.All offline_access'.
    }
    
    try:
        # Connect directly to Microsoft without proxy for better reliability.
        response = requests.post(TOKEN_URL, data=data, timeout=20, proxies={"http": None, "https": None})
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            print(f"❌ Failed to get Access Token: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Access Token request failed: {e}")
        return None

def generate_auth_string(user, token):
    return f"user={user}\1auth=Bearer {token}\1\1"

def extract_aws_code_from_email(msg, filters=None):
    """Extract a verification code from an email message."""
    try:
        subject = decode_header(msg["subject"])[0][0]
        if isinstance(subject, bytes):
            subject = subject.decode(errors='ignore')
        sender = str(msg.get("From", ""))
            
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                disposition = str(part.get("Content-Disposition"))
                if "attachment" not in disposition:
                    if content_type == "text/plain":
                        body += part.get_payload(decode=True).decode(errors='ignore')
                    elif content_type == "text/html":
                        # Basic HTML handling.
                        html = part.get_payload(decode=True).decode(errors='ignore')
                        body += html
        else:
            body = msg.get_payload(decode=True).decode(errors='ignore')
            
        full_text = f"{subject} {body}"
        
        if message_matches_filters(sender=sender, subject=subject, body=body, filters=filters):
            match = re.search(r'\b(\d{6})\b', full_text)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"Error parsing email: {e}")
    return None

def get_verification_code_via_imap(email_address, access_token, timeout=120, filters=None):
    """
    Fetch a verification code through IMAP polling.
    """
    print(f"📧 Listening for verification code through Outlook IMAP ({email_address})...")
    start_time = time.time()
    
    mail = None
    try:
        mail = imaplib.IMAP4_SSL('outlook.office365.com')
        # OAuth2 authentication.
        auth_string = generate_auth_string(email_address, access_token)
        mail.authenticate('XOAUTH2', lambda x: auth_string)
        mail.select('INBOX')
    except Exception as e:
        print(f"❌ IMAP connection or authentication failed: {e}")
        return None

    # Poll for new messages.
    try:
        while time.time() - start_time < timeout:
            try:
                # Re-select the mailbox to refresh state.
                mail.select('INBOX')
                
                # Search all messages.
                status, messages = mail.search(None, 'ALL')
                if status == "OK":
                    message_ids = messages[0].split()
                    if message_ids:
                        # Check the newest messages first.
                        for msg_id in reversed(message_ids[-3:]):
                            status, msg_data = mail.fetch(msg_id, '(RFC822)')
                            if status == "OK":
                                msg = email.message_from_bytes(msg_data[0][1])
                                code = extract_aws_code_from_email(msg, filters=filters)
                                if code:
                                    print(f"✅ Extracted Outlook verification code: {code}")
                                    return code
            except Exception as outer_e:
                print(f"Polling error: {outer_e}")

            time.sleep(5)
            
    except Exception as e:
        print(f"⚠️ IMAP polling error: {e}")
    finally:
        try:
            if mail: mail.logout()
        except: pass
        
    print("❌ Timed out waiting for Outlook email")
    return None

def get_verification_code_from_outlook(account_info, filters=None):
    """
    Main entry point.
    :param account_info: Dictionary containing email, client_id, and refresh_token.
    """
    email_addr = account_info.get('email')
    client_id = account_info.get('client_id')
    refresh_token = account_info.get('refresh_token')
    
    if not email_addr or not client_id or not refresh_token:
        print("❌ Account info is incomplete; cannot fetch verification code")
        return None
        
    print(f"🔄 Refreshing Access Token ({email_addr})...")
    access_token = get_access_token(refresh_token, client_id)
    
    if access_token:
        print("✅ Access Token acquired")
        return get_verification_code_via_imap(email_addr, access_token, filters=filters)
    else:
        print("❌ Failed to get Access Token; check whether the refresh token expired")
        return None
