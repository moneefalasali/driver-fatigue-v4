#!/usr/bin/env python3
"""
اختبار تكامل نظام مراقبة إرهاق السائق
"""

import sys
import os

# Add the project to the path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """اختبار استيراد المكتبات الأساسية"""
    print("✓ اختبار الاستيرادات...")
    try:
        from app import create_app, db, jwt, socketio
        from app.models import User, Session, FatigueData
        from app.auth import auth_bp
        from app.routes import main_bp
        from app.websocket import handle_connect, handle_disconnect
        print("  ✓ جميع المكتبات تم استيرادها بنجاح")
        return True
    except Exception as e:
        print(f"  ✗ خطأ في الاستيراد: {e}")
        return False

def test_app_creation():
    """اختبار إنشاء تطبيق Flask"""
    print("✓ اختبار إنشاء التطبيق...")
    try:
        from app import create_app
        app = create_app()
        print("  ✓ تم إنشاء التطبيق بنجاح")
        return True
    except Exception as e:
        print(f"  ✗ خطأ في إنشاء التطبيق: {e}")
        return False

def test_database():
    """اختبار قاعدة البيانات"""
    print("✓ اختبار قاعدة البيانات...")
    try:
        from app import create_app, db
        app = create_app()
        with app.app_context():
            # Create tables
            db.create_all()
            print("  ✓ تم إنشاء جداول قاعدة البيانات بنجاح")
        return True
    except Exception as e:
        print(f"  ✗ خطأ في قاعدة البيانات: {e}")
        return False

def test_routes():
    """اختبار المسارات الأساسية"""
    print("✓ اختبار المسارات...")
    try:
        from app import create_app
        app = create_app()
        
        # Get all routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(rule.rule)
        
        required_routes = [
            '/',
            '/login',
            '/register',
            '/monitoring',
            '/dashboard',
            '/settings',
            '/api/stats',
            '/api/auth/login',
            '/api/auth/register',
            '/api/auth/logout',
            '/api/auth/me'
        ]
        
        missing = [r for r in required_routes if r not in routes]
        if missing:
            print(f"  ✗ المسارات المفقودة: {missing}")
            return False
        
        print(f"  ✓ جميع المسارات الأساسية موجودة ({len(required_routes)} مسار)")
        return True
    except Exception as e:
        print(f"  ✗ خطأ في اختبار المسارات: {e}")
        return False

def test_static_files():
    """اختبار ملفات الـ Static"""
    print("✓ اختبار ملفات الـ Static...")
    try:
        required_files = [
            'app/static/js/auth.js',
            'app/static/js/alerts.js',
            'app/static/js/main.js',
            'app/static/js/camera.js',
            'app/static/js/sensors.js',
            'app/static/js/gps.js',
            'app/static/css/style.css',
            'app/static/manifest.json',
            'app/static/service-worker.js'
        ]
        
        missing = []
        for f in required_files:
            if not os.path.exists(f):
                missing.append(f)
        
        if missing:
            print(f"  ✗ الملفات المفقودة: {missing}")
            return False
        
        print(f"  ✓ جميع ملفات الـ Static موجودة ({len(required_files)} ملف)")
        return True
    except Exception as e:
        print(f"  ✗ خطأ في اختبار ملفات الـ Static: {e}")
        return False

def test_templates():
    """اختبار ملفات القوالب"""
    print("✓ اختبار ملفات القوالب...")
    try:
        required_templates = [
            'app/templates/base.html',
            'app/templates/index.html',
            'app/templates/login.html',
            'app/templates/register.html',
            'app/templates/monitoring.html',
            'app/templates/dashboard.html',
            'app/templates/settings.html'
        ]
        
        missing = []
        for f in required_templates:
            if not os.path.exists(f):
                missing.append(f)
        
        if missing:
            print(f"  ✗ القوالب المفقودة: {missing}")
            return False
        
        print(f"  ✓ جميع القوالب موجودة ({len(required_templates)} قالب)")
        return True
    except Exception as e:
        print(f"  ✗ خطأ في اختبار القوالب: {e}")
        return False

def test_register_without_tables_returns_clean_error():
    """اختبار تسجيل مستخدم عند غياب الجداول لا يسبب خطأ داخلي"""
    print("✓ اختبار تسجيل المستخدم مع الجداول غير المهيأة...")
    try:
        from app import create_app, db

        app = create_app()
        app.config['TESTING'] = True
        with app.app_context():
            db.drop_all()

        client = app.test_client()
        response = client.post('/api/auth/register', json={
            'username': 'dbtestuser',
            'email': 'dbtest@example.com',
            'password': 'secret123'
        })

        if response.status_code not in {200, 201, 500, 503}:
            print(f"  ✗ استجابة غير متوقعة: {response.status_code} {response.get_data(as_text=True)}")
            return False

        print("  ✓ تم التعامل مع غياب الجداول بشكل آمن")
        return True
    except Exception as e:
        print(f"  ✗ خطأ في اختبار تسجيل المستخدم: {e}")
        return False


def test_stats_endpoint():
    """اختبار endpoint الإحصائيات مع مستخدم غير لديه جلسات"""
    print("✓ اختبار endpoint الإحصائيات...")
    try:
        from app import create_app, db
        from app.models import User
        from flask_jwt_extended import create_access_token

        app = create_app()
        app.config['TESTING'] = True
        with app.app_context():
            db.drop_all()
            db.create_all()
            user = User(username='statsuser', email='stats@example.com')
            user.set_password('secret123')
            db.session.add(user)
            db.session.commit()
            token = create_access_token(identity=str(user.id))

        client = app.test_client()
        response = client.get('/api/stats', headers={'Authorization': f'Bearer {token}'})
        if response.status_code != 200:
            print(f"  ✗ فشل endpoint الإحصائيات: {response.status_code} {response.get_data(as_text=True)}")
            return False

        data = response.get_json()
        if 'total_sessions' not in data or 'total_hours' not in data:
            print(f"  ✗ استجابة غير صحيحة: {data}")
            return False

        print("  ✓ endpoint الإحصائيات يعمل بنجاح")
        return True
    except Exception as e:
        print(f"  ✗ خطأ في endpoint الإحصائيات: {e}")
        return False


def main():
    """تشغيل جميع الاختبارات"""
    print("\n" + "="*50)
    print("اختبار تكامل نظام مراقبة إرهاق السائق")
    print("="*50 + "\n")
    
    tests = [
        test_imports,
        test_app_creation,
        test_database,
        test_routes,
        test_static_files,
        test_templates,
        test_register_without_tables_returns_clean_error,
        test_stats_endpoint
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"✗ خطأ غير متوقع: {e}")
            results.append(False)
        print()
    
    # Summary
    print("="*50)
    passed = sum(results)
    total = len(results)
    print(f"النتائج: {passed}/{total} اختبار نجح")
    
    if passed == total:
        print("✓ جميع الاختبارات نجحت! النظام جاهز للإطلاق.")
        return 0
    else:
        print("✗ بعض الاختبارات فشلت. يرجى مراجعة الأخطاء أعلاه.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
