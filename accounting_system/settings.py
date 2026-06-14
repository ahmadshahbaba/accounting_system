"""
Django settings for accounting_system project.
"""

from pathlib import Path
import os

# مسیر پایه پروژه
BASE_DIR = Path(__file__).resolve().parent.parent

# 🔐 امنیت - کلید مخفی (در محیط واقعی حتماً یک کلید قوی و تصادفی قرار بده)
SECRET_KEY = 'django-insecure-YourSecretKeyHere123!@#$%^&*()'

# 🚨 حالت DEBUG - در محیط تولید حتماً False باشد
DEBUG = False

# 🌐 میزبان‌های مجاز (دامنه خود را اینجا وارد کن)
ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = [
    'https://web-production-c0c10.up.railway.app',
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # اپلیکیشن‌های سفارشی
    'inventory',
    'sales',
    'purchases',
    'customers',
    'suppliers',
    'misc_persons',
    'transactions',
    'expenses',
    'settings_app',
    'common',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # 'django.middleware.locale.LocaleMiddleware',  # کامنت شد (غیرفعال برای حذف چندزبانی)
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)
ROOT_URLCONF = 'accounting_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # 'django.template.context_processors.i18n',  # کامنت شد (غیرفعال)
            ],
        },
    },
]

WSGI_APPLICATION = 'accounting_system.wsgi.application'

# ========== پایگاه داده (Database) ==========
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# اعتبارسنجی رمز عبور
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ========== زبان و زمان (فقط فارسی) ==========
LANGUAGE_CODE = 'fa'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True  # فعال بودن i18n (مهم نیست چون فقط یک زبان داریم)
USE_L10N = True
USE_TZ = True

# حذف لیست زبان‌های دیگر (فقط فارسی)
# LANGUAGES = [('fa', 'فارسی')]  # نیازی به تعریف نیست چون فقط یک زبان داریم

# مسیر فایل‌های ترجمه (اختیاری - در صورت نیاز می‌توانی پوشه locale را حذف کنی)
LOCALE_PATHS = [BASE_DIR / 'locale']

# ========== فایل‌های استاتیک و رسانه ==========
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ========== تنظیمات ورود و خروج ==========
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# ========== تنظیمات نشست (Session) ==========
SESSION_EXPIRE_AT_BROWSER_CLOSE = True   # با بستن مرورگر، کاربر خارج می‌شود
SESSION_COOKIE_AGE = 1209600
SESSION_SAVE_EVERY_REQUEST = False

CSRF_TRUSTED_ORIGINS = [
    'https://*.railway.app',
    'https://web-production-c0c10.up.railway.app'
]
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True