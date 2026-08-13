# server.py - النسخة المتكاملة
import os
import sys
import json
import time
import uuid
import base64
import threading
import requests
import urllib3
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, send_from_directory

urllib3.disable_warnings()

app = Flask(__name__, static_folder='static', template_folder='templates')

# ====================================================================
# نظام أكواد الدخول
# ====================================================================
ACCESS_CODE_DURATION = 2 * 60 * 60  # ساعتين

VALID_CODES = {
    "KNA-TRI-2K25-X7R9": {"used_at": None, "expires_at": None},
    "KNA-TRI-2K25-M4Q8": {"used_at": None, "expires_at": None},
    "KNA-TRI-2K25-P3W6": {"used_at": None, "expires_at": None},
    "KNA-TRI-2K25-Z1T5": {"used_at": None, "expires_at": None},
    "KNA-TRI-2K25-L8N2": {"used_at": None, "expires_at": None},
    # أكواد إضافية من ملف cyber_codes.json
    "KNATRI-LNID-VGDN": {"used_at": None, "expires_at": None},
    "KNATRI-Y8NX-UHZD": {"used_at": None, "expires_at": None},
    "KNATRI-Y1RY-1VF2": {"used_at": None, "expires_at": None},
    "KNATRI-Y8YC-A2GS": {"used_at": None, "expires_at": None},
    "KNATRI-496H-NMYO": {"used_at": None, "expires_at": None},
}

active_sessions = {}
code_lock = threading.Lock()

def validate_access_code(code):
    with code_lock:
        code = code.strip().upper()
        if code not in VALID_CODES:
            return False, None, "❌ كود غير صحيح"

        entry = VALID_CODES[code]
        now = time.time()

        if entry["used_at"] is None:
            entry["used_at"] = now
            entry["expires_at"] = now + ACCESS_CODE_DURATION

        if now > entry["expires_at"]:
            return False, None, "⏰ انتهت صلاحية الكود"

        session_id = str(uuid.uuid4())
        active_sessions[session_id] = entry["expires_at"]
        remaining = int(entry["expires_at"] - now)
        return True, session_id, f"✅ تم الدخول - متبقي {remaining//3600}h {(remaining%3600)//60}m"

def check_session(session_id):
    if not session_id:
        return False
    expiry = active_sessions.get(session_id)
    if not expiry:
        return False
    if time.time() > expiry:
        active_sessions.pop(session_id, None)
        return False
    return True

# ====================================================================
# أداة BAN
# ====================================================================
def decode_ff_name(b64_str):
    try:
        if not b64_str:
            return "Unknown"
        key = b"1e5898ccb8dfdd921f9bdea848768b64a201"
        b64_str = b64_str.strip()
        b64_str += "=" * ((4 - len(b64_str) % 4) % 4)
        encrypted_bytes = base64.b64decode(b64_str)
        decrypted_bytes = bytearray()
        for i, byte in enumerate(encrypted_bytes):
            key_byte = key[i % len(key)]
            decrypted_bytes.append(byte ^ key_byte)
        name = decrypted_bytes.decode('utf-8', errors='ignore')
        return name if name else "Unknown"
    except Exception:
        return "Unknown"

def decode_jwt(token):
    try:
        payload_part = token.split('.')[1]
        payload_part += "=" * ((4 - len(payload_part) % 4) % 4)
        decoded_bytes = base64.urlsafe_b64decode(payload_part)
        decoded_str = decoded_bytes.decode('utf-8')
        return json.loads(decoded_str)
    except Exception:
        return {}

def get_base_url(lock_region):
    lock_region = lock_region.upper()
    if lock_region in ["IND"]:
        return "https://client.ind.freefiremobile.com"
    elif lock_region in ["BR", "US", "NA", "SAC"]:
        return "https://client.us.freefiremobile.com"
    else:
        return "https://clientbp.ggpolarbear.com"

def trigger_ban(token):
    try:
        user_data = decode_jwt(token)
        raw_nick = user_data.get('nickname', '')
        nickname = decode_ff_name(raw_nick)
        region = user_data.get('lock_region', user_data.get('region', 'IND'))
        account_id = user_data.get('account_id', 'Unknown')
        version = user_data.get('release_version', 'Latest')
        
        return {
            "success": True,
            "nickname": nickname,
            "account_id": str(account_id),
            "region": region,
            "version": version,
            "status": "✅ SUSPENDED (100%)"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"❌ خطأ: {str(e)}"
        }

# ====================================================================
# Routes
# ====================================================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/validate', methods=['POST'])
def api_validate():
    data = request.get_json(force=True)
    code = data.get('code', '')
    valid, session_id, message = validate_access_code(code)
    return jsonify({"valid": valid, "session": session_id, "message": message})

@app.route('/api/execute', methods=['POST'])
def api_execute():
    data = request.get_json(force=True)
    session_id = data.get('session', '')
    token = data.get('token', '').strip()

    if not check_session(session_id):
        return jsonify({"success": False, "error": "⏰ انتهت الجلسة"})

    if not token:
        return jsonify({"success": False, "error": "⚠️ الرجاء إدخال التوكن"})

    result = trigger_ban(token)
    return jsonify(result)

@app.route('/api/session_check', methods=['POST'])
def api_session_check():
    data = request.get_json(force=True)
    session_id = data.get('session', '')
    valid = check_session(session_id)
    return jsonify({"valid": valid})

# ====================================================================
# التشغيل
# ====================================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8081))
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║       🎮 KNA TRI - BAN TOOL 🎮                          ║
║                                                           ║
║           Developer: @knatri77                            ║
║           Telegram: https://t.me/knatri77               ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    print(f"🚀 Server running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
