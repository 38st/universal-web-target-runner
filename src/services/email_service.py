"""
Email service module.
Implements temporary mailbox support using the cloudflare_temp_email project.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import random
import string
import time
import email
from email import policy

from config import (
    EMAIL_WORKER_URL,
    EMAIL_DOMAIN,
    EMAIL_PREFIX_LENGTH,
    EMAIL_WAIT_TIMEOUT,
    EMAIL_POLL_INTERVAL,
    HTTP_TIMEOUT
)
from helpers.utils import http_session, get_user_agent, extract_verification_code


DEFAULT_VERIFICATION_FILTERS = {
    "sender_contains": ["amazon", "aws"],
    "subject_contains": ["verify"],
    "body_contains": ["amazon", "aws", "verify"],
}


def _contains_any(text: str, values: list[str]) -> bool:
    haystack = (text or "").lower()
    return any(str(value).lower() in haystack for value in values if value)


def message_matches_filters(
    *,
    sender: str = "",
    subject: str = "",
    body: str = "",
    filters: dict | None = None,
) -> bool:
    """Return True when a message matches configured verification filters."""

    active_filters = DEFAULT_VERIFICATION_FILTERS if filters is None else filters
    sender_contains = list(active_filters.get("sender_contains") or [])
    subject_contains = list(active_filters.get("subject_contains") or [])
    body_contains = list(active_filters.get("body_contains") or [])

    if not sender_contains and not subject_contains and not body_contains:
        return True

    return (
        _contains_any(sender, sender_contains)
        or _contains_any(subject, subject_contains)
        or _contains_any(body, body_contains)
    )


def create_temp_email():
    """
    Create a temporary mailbox.
    Returns: (email address, JWT token), or (None, None) on failure.
    """
    print("Creating temporary mailbox...")

    prefix = ''.join(random.choices(
        string.ascii_lowercase + string.digits,
        k=EMAIL_PREFIX_LENGTH
    ))

    headers = {
        "Content-Type": "application/json",
        "User-Agent": get_user_agent()
    }

    try:
        response = http_session.post(
            f"{EMAIL_WORKER_URL}/api/new_address",
            headers=headers,
            json={"name": prefix},
            timeout=HTTP_TIMEOUT
        )

        if response.status_code == 200:
            result = response.json()
            jwt_token = result.get('jwt')
            actual_email = result.get('address')

            if jwt_token and actual_email:
                print(f"Mailbox created: {actual_email}")
                return actual_email, jwt_token
            elif jwt_token:
                fallback_email = f"tmp{prefix}@{EMAIL_DOMAIN}"
                print(f"Mailbox created: {fallback_email}")
                return fallback_email, jwt_token
        else:
            print(f"API error: HTTP {response.status_code}")

    except Exception as e:
        print(f"Mailbox creation failed: {e}")

    return None, None


def fetch_emails(jwt_token: str):
    """Fetch mailbox messages."""
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "User-Agent": get_user_agent()
    }
    
    try:
        response = http_session.get(
            f"{EMAIL_WORKER_URL}/api/mails?limit=20&offset=0",
            headers=headers,
            timeout=HTTP_TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                return result.get('results', result.get('mails', []))
                
    except Exception as e:
        print(f"  Email fetch error: {e}")
    
    return None


def get_email_detail(jwt_token: str, email_id: str):
    """Fetch email details."""
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "User-Agent": get_user_agent()
    }
    
    try:
        response = http_session.get(
            f"{EMAIL_WORKER_URL}/api/mails/{email_id}",
            headers=headers,
            timeout=HTTP_TIMEOUT
        )
        
        if response.status_code == 200:
            return response.json()
            
    except Exception as e:
        print(f"  Email detail fetch error: {e}")
    
    return None


def parse_raw_email(raw_content: str):
    """Parse raw email content."""
    result = {'subject': '', 'body': '', 'sender': ''}
    
    if not raw_content:
        return result
    
    try:
        msg = email.message_from_string(raw_content, policy=policy.default)
        result['subject'] = msg.get('Subject', '')
        result['sender'] = msg.get('From', '')
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type in ['text/plain', 'text/html']:
                    payload = part.get_payload(decode=True)
                    if payload:
                        result['body'] = payload.decode('utf-8', errors='ignore')
                        break
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                result['body'] = payload.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  Email parse error: {e}")
    
    return result


def wait_for_verification_email(jwt_token: str, timeout: int = None, filters: dict | None = None):
    """
    Wait for and extract a verification code.
    Returns the code string, or None when not found.
    """
    if timeout is None:
        timeout = EMAIL_WAIT_TIMEOUT
    
    print(f"Waiting for verification email (up to {timeout} seconds)...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        emails = fetch_emails(jwt_token)
        
        if emails and len(emails) > 0:
            for email_item in emails:
                raw_content = email_item.get('raw', '')
                if raw_content:
                    parsed = parse_raw_email(raw_content)
                    subject = parsed['subject']
                    sender = parsed['sender'].lower()
                    body = parsed['body']
                else:
                    sender = str(email_item.get('from') or email_item.get('source', '')).lower()
                    subject = email_item.get('subject', '') or ''
                    body = ''
                
                if message_matches_filters(sender=sender, subject=subject, body=body, filters=filters):
                    print("\nVerification email received!")
                    print(f"   Subject: {subject}")
                    
                    code = extract_verification_code(subject)
                    if code:
                        return code
                    
                    if body:
                        code = extract_verification_code(body)
                        if code:
                            return code
                    
                    email_id = email_item.get('id')
                    if email_id:
                        detail = get_email_detail(jwt_token, email_id)
                        if detail:
                            detail_raw = detail.get('raw', '')
                            if detail_raw:
                                parsed_detail = parse_raw_email(detail_raw)
                                code = extract_verification_code(parsed_detail['body'])
                                if code:
                                    return code
                            
                            content = (
                                detail.get('html') or 
                                detail.get('text') or 
                                detail.get('content', '')
                            )
                            if content:
                                code = extract_verification_code(content)
                                if code:
                                    return code
        
        elapsed = int(time.time() - start_time)
        print(f"  Waiting... ({elapsed}s)", end='\r')
        time.sleep(EMAIL_POLL_INTERVAL)
    
    print("\nTimed out waiting for verification email")
    return None
