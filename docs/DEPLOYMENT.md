# GULA Platform - دليل النشر الكامل

## الخطوات من الصفر حتى الإنتاج

---

## 1. إنشاء السيرفر في DigitalOcean

| الإعداد | القيمة المقترحة |
|---------|----------------|
| Image | Ubuntu 22.04 LTS |
| Size | Basic - 2 GB RAM / 2 vCPU ($18/mo) |
| Region | اختر الأقرب لجمهورك |
| Authentication | SSH Key (يُفضل) أو Password |

---

## 2. إعداد السيرفر (مرة واحدة فقط)

بعد إنشاء الـ Droplet، اتصل بـ SSH وشغّل:

```bash
# اتصل بالسيرفر
ssh root@YOUR_SERVER_IP

# شغّل سكريبت الإعداد الكامل
curl -fsSL https://raw.githubusercontent.com/samertts/gula-platform/main/scripts/server-setup.sh | sudo bash
```

السكريبت سيقوم بـ:
- ✅ تثبيت Docker + Nginx + Certbot
- ✅ إنشاء مستخدم `samertts`
- ✅ توليد SSH key للـ deployment
- ✅ استنساخ المشروع
- ✅ إعداد الـ nginx
- ✅ إعداد الـ firewall (UFW)
- ✅ إنشاء ملف `.env`
- ✅ **طباعة GitHub Secrets التي تحتاجها**

---

## 3. إضافة GitHub Secrets

بعد تشغيل السكريبت، ستظهر لك 3 قيم. أضفها في:

**GitHub → Repository → Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | القيمة |
|-------------|--------|
| `SERVER_HOST` | IP السيرفر (مثل `167.71.xxx.xxx`) |
| `SERVER_USER` | `samertts` |
| `SERVER_SSH_KEY` | المفتاح الخاص كاملاً (يبدأ بـ `-----BEGIN OPENSSH PRIVATE KEY-----`) |

---

## 4. أول عملية نشر

```bash
# على جهازك المحلي
git checkout main
git push origin main
```

GitHub Actions سيقوم تلقائياً بـ:
1. Build الـ Docker images
2. SSH للسيرفر
3. Pull آخر تحديث
4. إعادة تشغيل الخدمات
5. Health check

---

## 5. إعداد SSL (اختياري - بعد أول نشر)

```bash
# على السيرفر
sudo certbot --nginx -d gula-platform.org -d www.gula-platform.org

# نسخ الـ config الجديد (مع HTTPS)
sudo cp /home/samertts/gula-platform/config/nginx/system/gula-platform.conf \
        /etc/nginx/sites-available/gula-platform
sudo nginx -t && sudo systemctl reload nginx
```

---

## 6. أوامر مفيدة على السيرفر

```bash
# حالة الخدمات
cd ~/gula-platform && docker compose ps

# عرض الـ logs
docker compose logs -f gula-backend
docker compose logs -f gula-api-gateway

# إعادة تشغيل
docker compose restart

# تحديث يدوي (بدون GitHub Actions)
cd ~/gula-platform
git pull origin main
./deploy.sh

# فحص الصحة
curl http://localhost:8080/health
```

---

## 7. تنظيف الفروع القديمة من GitHub

```bash
# احذف الفروع المدموجة (codex/* و claude/* القديمة)
git fetch -p origin

# اعرض الفروع المدموجة
git branch -r --merged main | grep -v main

# احذف واحداً واحداً
git push origin --delete claude/arabic-greeting-lDwg6
git push origin --delete claude/merge-to-main-lDwg6
git push origin --delete claude/setup-gula-platform-GTh4t
```

---

## مهم: أمان التوكن

بعد الإعداد:
1. **احذف** توكن DigitalOcean الذي شاركته
2. **أنشئ** توكناً جديداً من: `cloud.digitalocean.com/account/api/tokens`
3. لا تشارك التوكنات أبداً في صور أو نصوص
