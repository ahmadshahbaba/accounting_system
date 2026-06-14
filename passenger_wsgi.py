import sys
import os

# مسیر مطلق به پوشه پروژه‌تان را اینجا تنظیم کنید
# برای نمونه، اگر پروژه در public_html/accounting_system است، مسیر را به آن بدهید.
path = '/home/your_username/public_html/accounting_system'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'accounting_system.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()