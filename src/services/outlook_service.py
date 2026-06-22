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
    使用 refresh_token 获取 access_token
    """
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
        # 有些特殊的 client_id 可能不需要 scope，或者默认 scope 即可
        # 如果报错，可以尝试添加 scope='https://outlook.office.com/IMAP.AccessAsUser.All offline_access'
    }
    
    try:
        # 直连微软，不走代理（更加稳定）
        response = requests.post(TOKEN_URL, data=data, timeout=20, proxies={"http": None, "https": None})
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            print(f"❌ 获取 Access Token 失败: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 请求 Access Token 异常: {e}")
        return None

def generate_auth_string(user, token):
    return f"user={user}\1auth=Bearer {token}\1\1"

def extract_aws_code_from_email(msg, filters=None):
    """从邮件对象中提取 AWS 验证码"""
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
                        # 简单处理 HTML
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
        print(f"解析邮件出错: {e}")
    return None

def get_verification_code_via_imap(email_address, access_token, timeout=120, filters=None):
    """
    通过 IMAP 获取 AWS 验证码 (轮询)
    """
    print(f"📧 开始通过 Outlook IMAP 监听验证码 ({email_address})...")
    start_time = time.time()
    
    mail = None
    try:
        mail = imaplib.IMAP4_SSL('outlook.office365.com')
        # OAuth2 认证
        auth_string = generate_auth_string(email_address, access_token)
        mail.authenticate('XOAUTH2', lambda x: auth_string)
        mail.select('INBOX')
    except Exception as e:
        print(f"❌ IMAP 连接或认证失败: {e}")
        return None

    # 轮询
    try:
        while time.time() - start_time < timeout:
            try:
                # 重新 select 刷新状态
                mail.select('INBOX')
                
                # 搜索所有邮件
                status, messages = mail.search(None, 'ALL')
                if status == "OK":
                    message_ids = messages[0].split()
                    if message_ids:
                        # 从最新的开始查 (最后 3 封)
                        for msg_id in reversed(message_ids[-3:]):
                            status, msg_data = mail.fetch(msg_id, '(RFC822)')
                            if status == "OK":
                                msg = email.message_from_bytes(msg_data[0][1])
                                code = extract_aws_code_from_email(msg, filters=filters)
                                if code:
                                    print(f"✅ 成功提取 Outlook 验证码: {code}")
                                    return code
            except Exception as outer_e:
                print(f"轮询中出错: {outer_e}")

            time.sleep(5)
            
    except Exception as e:
        print(f"⚠️ IMAP 轮询出错: {e}")
    finally:
        try:
            if mail: mail.logout()
        except: pass
        
    print("❌ 等待 Outlook 邮件超时")
    return None

def get_verification_code_from_outlook(account_info, filters=None):
    """
    主入口
    :param account_info: 包含 email, client_id, refresh_token 的字典
    """
    email_addr = account_info.get('email')
    client_id = account_info.get('client_id')
    refresh_token = account_info.get('refresh_token')
    
    if not email_addr or not client_id or not refresh_token:
        print("❌ 账号信息不完整，无法获取验证码")
        return None
        
    print(f"🔄 正在刷新 Access Token ({email_addr})...")
    access_token = get_access_token(refresh_token, client_id)
    
    if access_token:
        print("✅ Access Token 获取成功")
        return get_verification_code_via_imap(email_addr, access_token, filters=filters)
    else:
        print("❌ Access Token 获取失败，请检查 Refresh Token 是否过期")
        return None
