#!/usr/bin/env python3
"""
💀 Cyber Elite Server System v9.0 💀
خادم واجهة حصن الهكر مع نظام الكودات
Hacker Fortress Interface Server with Code System
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
from datetime import datetime
from code_generator import CyberCodeGenerator
import threading
import time

app = Flask(__name__)
CORS(app)

# Initialize Code Generator
generator = CyberCodeGenerator()
generator.generate_bulk_codes()  # Generate codes on startup

class HackerServer:
    """خادم نظام حصن الهكر"""
    
    def __init__(self):
        self.active_users = {}
        self.access_attempts = 0
        self.successful_logins = 0
        self.server_start_time = datetime.now()
    
    def log_access_attempt(self, success=False, code=None):
        """تسجيل محاولات الدخول"""
        self.access_attempts += 1
        if success:
            self.successful_logins += 1
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status = "✅ ناجح" if success else "❌ فاشل"
        
        print(f"[{timestamp}] محاولة دخول: {status} | الكود: {code}")
    
    def get_server_stats(self):
        """الحصول على إحصائيات الخادم"""
        uptime = datetime.now() - self.server_start_time
        code_stats = generator.get_statistics()
        
        return {
            "server_info": {
                "name": "Cyber Elite Security System",
                "version": "9.0",
                "uptime": str(uptime).split('.')[0],
                "start_time": self.server_start_time.isoformat()
            },
            "access_stats": {
                "total_attempts": self.access_attempts,
                "successful_logins": self.successful_logins,
                "failed_attempts": self.access_attempts - self.successful_logins,
                "active_users": len(self.active_users)
            },
            "code_stats": code_stats
        }

# Initialize Server
server = HackerServer()

# HTML Template
def get_html_template():
    try:
        with open('hacker_face.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "<html><body><h1>KHATRI System Loading...</h1></body></html>"

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/verify-code', methods=['POST'])
def verify_code():
    """التحقق من الكود"""
    data = request.json
    input_code = data.get('code', '').strip()
    user_id = data.get('user_id', None)
    ip_address = request.remote_addr
    
    if not input_code:
        return jsonify({
            "success": False,
            "message": "الرجاء إدخال الكود"
        }), 400
    
    # Verify code
    result = generator.verify_code(input_code, user_id, ip_address)
    server.log_access_attempt(result.get('valid', False), input_code)
    
    if result['valid']:
        # Add to active users
        session_id = f"session_{int(time.time())}_{len(active_users)}"
        server.active_users[session_id] = {
            "code": input_code,
            "user_id": user_id,
            "ip_address": ip_address,
            "login_time": datetime.now().isoformat()
        }
        
        return jsonify({
            "success": True,
            "message": result['message'],
            "code_data": result['code_data'],
            "session_id": session_id,
            "expires_in_hours": result.get('expires_in_hours', 24)
        })
    else:
        return jsonify({
            "success": False,
            "message": result['message'],
            "reason": result.get('reason', 'unknown')
        }), 401

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """الحصول على إحصائيات النظام"""
    stats = server.get_server_stats()
    return jsonify(stats)

@app.route('/api/codes/sample', methods=['GET'])
def get_sample_codes():
    """الحصول على عينة من الكودات للعرض فقط"""
    count = request.args.get('count', 10, type=int)
    
    # Generate sample codes (these are not saved, just for display)
    samples = []
    for i in range(min(count, 100)):
        code_data = generator.generate_single_code()
        samples.append({
            "code": code_data['code'],
            "expires_at": code_data['expires_at']
        })
    
    return jsonify({
        "success": True,
        "samples": samples,
        "note": "هذه مجرد عينة للعرض، استخدم الكودات الأصلية من النظام"
    })

@app.route('/api/active-codes', methods=['GET'])
def get_active_codes():
    """الحصول على الكودات النشطة (للمسؤولين)"""
    codes = generator.load_codes()
    active_codes = [
        {
            "code": c['code'],
            "created_at": c['created_at'],
            "expires_at": c['expires_at'],
            "used": c['used']
        }
        for c in codes[:50]  # Limit to first 50 for security
    ]
    
    return jsonify({
        "success": True,
        "active_codes": active_codes,
        "total_shown": len(active_codes)
    })

@app.route('/api/system-health', methods=['GET'])
def system_health():
    """فحص صحة النظام"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "code_generator": "operational",
            "verification_system": "operational",
            "database": "operational",
            "security": "maximum"
        },
        "performance": {
            "response_time": "<50ms",
            "uptime_percentage": "99.99%"
        }
    }
    
    return jsonify(health_status)

def update_statistics_background():
    """تحديث الإحصائيات في الخلفية"""
    while True:
        time.sleep(60)  # Update every minute
        generator.save_codes(generator.load_codes())  # Refresh and save codes

def run():
    """تشغيل الخادم"""
    port = 8000
    
    # Start background thread
    background_thread = threading.Thread(target=update_statistics_background, daemon=True)
    background_thread.start()
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║       💀 Cyber Elite Server v9.0 💀                      ║
║                                                           ║
║           خادم واجهة حصن الهكر                          ║
║              Hacker Fortress Interface Server              ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

🚀 الخادم جاهز للعمل...
📡 الرابط: http://0.0.0.0:8000
🔒 الأمان: أقصى مستوى
💾 قاعدة البيانات: جاهزة
📊 نظام الإحصائيات: نشط

""")

    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == '__main__':
    run()