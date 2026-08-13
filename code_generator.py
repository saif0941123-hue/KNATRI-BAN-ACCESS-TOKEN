#!/usr/bin/env python3
"""
💀 Cyber Elite Code Generator System v9.0 💀
مولد الكودات الآمن والمشفر
Secure Code Generator System
"""

import json
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from pathlib import Path
import random
import string

class CyberCodeGenerator:
    """نظام توليد الكودات الأمنية المتقدم"""
    
    def __init__(self):
        self.prefix = "KNATRI"
        self.total_codes = 1000
        self.code_length = 12
        self.validity_hours = 24
        self.storage_file = "cyber_codes.json"
        self.log_file = "cyber_system.log"
        
    def generate_secure_hash(self, code):
        """توليد تشفير آمن للكود"""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256((code + salt).encode())
        return hash_obj.hexdigest(), salt
    
    def generate_segment(self, length=4):
        """توليد جزء عشوائي من الكود"""
        chars = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    def generate_single_code(self):
        """توليد كود واحد آمن"""
        segment1 = self.generate_segment()
        segment2 = self.generate_segment()
        code = f"{self.prefix}-{segment1}-{segment2}"
        
        # تحديد أوقات الصلاحية
        now = datetime.now()
        expires_at = now + timedelta(hours=self.validity_hours)
        
        # توليد التشفير
        hash_value, salt = self.generate_secure_hash(code)
        
        return {
            "code": code,
            "hash": hash_value,
            "salt": salt,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "used": False,
            "used_at": None,
            "user_id": None,
            "ip_address": None
        }
    
    def generate_bulk_codes(self, count=None):
        """توليد كمية كبيرة من الكودات"""
        if count is None:
            count = self.total_codes
        
        codes = []
        for i in range(count):
            code_data = self.generate_single_code()
            codes.append(code_data)
            
            # تسجيل الكود
            self.log_code(code_data, i + 1)
        
        # حفظ الكودات
        self.save_codes(codes)
        
        return codes
    
    def save_codes(self, codes):
        """حفظ الكودات في م JSON"""
        data = {
            "system_name": "Cyber Elite Security System",
            "version": "9.0",
            "generated_at": datetime.now().isoformat(),
            "total_codes": len(codes),
            "validity_hours": self.validity_hours,
            "codes": codes
        }
        
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ تم حفظ {len(codes)} كود بنجاح في {self.storage_file}")
        except Exception as e:
            print(f"❌ خطأ في الحفظ: {e}")
    
    def load_codes(self):
        """تحميل الكودات من ملف JSON"""
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('codes', [])
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"❌ خطأ في التحميل: {e}")
            return []
    
    def log_code(self, code_data, index):
        """تسجيل الكود في ملف اللوج"""
        log_entry = f"""
[CODE #{index}] - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
┌─────────────────────────────────────┐
│  كود: {code_data['code']}
│  إنشاء: {code_data['created_at']}
│  انتهاء: {code_data['expires_at']}
│  الحالة: {'نشط' if not code_data['used'] else 'مستخدم'}
│  التشفير: {code_data['hash'][:16]}...
└─────────────────────────────────────┘
        """
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"❌ خطأ في التسجيل: {e}")
    
    def verify_code(self, input_code, user_id=None, ip_address=None):
        """التحقق من صحة الكود"""
        codes = self.load_codes()
        now = datetime.now()
        
        for code_data in codes:
            # البحث عن الكود
            if code_data['code'] == input_code.upper():
                # التحقق من الاستخدام
                if code_data['used']:
                    return {
                        "valid": False,
                        "message": "هذا الكود مستخدم بالفعل!",
                        "reason": "already_used"
                    }
                
                # التحقق من الصلاحية
                expires_at = datetime.fromisoformat(code_data['expires_at'])
                if now > expires_at:
                    return {
                        "valid": False,
                        "message": "الكود منتهي الصلاحية!",
                        "reason": "expired"
                    }
                
                # الكود صحيح - تحديث الحالة
                code_data['used'] = True
                code_data['used_at'] = now.isoformat()
                code_data['user_id'] = user_id
                code_data['ip_address'] = ip_address
                
                # حفظ التحديثات
                self.save_codes(codes)
                
                # تسجيل الاستخدام
                self.log_code_usage(code_data)
                
                return {
                    "valid": True,
                    "message": "تم التحقق من الكود بنجاح!",
                    "code_data": code_data,
                    "expires_in_hours": (expires_at - now).total_seconds() / 3600
                }
        
        return {
            "valid": False,
            "message": "الكود غير موجود!",
            "reason": "not_found"
        }
    
    def log_code_usage(self, code_data):
        """تسجيل استخدام الكود"""
        log_entry = f"""
[CODE USED] - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
┌─────────────────────────────────────┐
│  كود: {code_data['code']}
│  مرات الاستخدام: 1 (ثابت)
│  وقت الاستخدام: {code_data['used_at']}
│  معرف المستخدم: {code_data['user_id']}
│  IP: {code_data['ip_address']}
└─────────────────────────────────────┘
🔒 تم استخدام الكود وتعطيله
        """
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def get_statistics(self):
        """الحصول على إحصائيات النظام"""
        codes = self.load_codes()
        now = datetime.now()
        
        total = len(codes)
        used = len([c for c in codes if c['used']])
        expired = len([c for c in codes if c['used'] and datetime.fromisoformat(c['expires_at']) < now])
        active = used - expired
        available = total - used
        
        return {
            "total_codes": total,
            "used_codes": used,
            "expired_codes": expired,
            "active_codes": active,
            "available_codes": available,
            "usage_percentage": (used / total * 100) if total > 0 else 0
        }
    
    def display_statistics(self):
        """عرض الإحصائيات بشكل جميل"""
        stats = self.get_statistics()
        
        print("""
╔═══════════════════════════════════════════════════════════╗
║         💀 إحصائيات نظام حصن الهكر 💀                     ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
""")
        print(f"""
║  📊 إجمالي الكودات:        {stats['total_codes']:<10}    ║
║  🎫 الكودات المتاحة:       {stats['available_codes']:<10}    ║
║  ✅ الكودات النشطة:        {stats['active_codes']:<10}    ║
║  ⏰ الكودات المنتهية:      {stats['expired_codes']:<10}    ║
║  📈 نسبة الاستخدام:        {stats['usage_percentage']:.1f}%{'':<11}    ║
""")
        print("""
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """)
    
    def generate_sample_codes(self, count=10):
        """توليد عينة من الكودات للعرض"""
        print("\n" + "="*60)
        print("💀 عينة من الكودات المتاحة: 💀")
        print("="*60 + "\n")
        
        codes = []
        for i in range(count):
            code_data = self.generate_single_code()
            codes.append(code_data)
            
            print(f"  {i+1}. 🎫 {code_data['code']}")
            print(f"      ⏰ ينتهي: {code_data['expires_at']}")
            print(f"      🔒 التشفير: {code_data['hash'][:20]}...")
            print()
        
        return codes

def main():
    """الوظيفة الرئيسية"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║       💀 Cyber Elite Code Generator v9.0 💀               ║
║                                                           ║
║           نظام توليد الكودات الأمنية المتقدم             ║
║              Advanced Secure Code Generator                ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)

    generator = CyberCodeGenerator()
    
    # توليد الكودات
    print("🔧 جاري توليد " + str(generator.total_codes) + " كود آمن...")
    print("⏳ قد يستغرق هذا بضع ثوانٍ...\n")
    
    codes = generator.generate_bulk_codes()
    
    print(f"\n✅ تم توليد {len(codes)} كود بنجاح!")
    print(f"✅ تم حفظ الكودات في: {generator.storage_file}")
    print(f"✅ تم حفظ السجلات في: {generator.log_file}\n")
    
    # عرض الإحصائيات
    generator.display_statistics()
    
    # عرض عينة من الكودات
    generator.generate_sample_codes(5)
    
    print("\n" + "="*60)
    print("🎉 النظام جاهز للاستخدام! 🎉")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()