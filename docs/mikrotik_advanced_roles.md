# MikroTik Advanced Roles

مستندات نقش‌های پیشرفته Phoenix V10 برای MikroTik hap ax3.

## 1. Smart Splitter (تقسیم‌کننده هوشمند ترافیک)

**هدف:** تشخیص ترافیک داخلی/خارجی و هدایت خودکار به مسیر مناسب.

**مزایا:**
- کاهش مصرف پهنای باند VPN
- افزایش سرعت دسترسی به سایت‌های داخلی
- کاهش بار روی سرورهای خارجی

**تنظیمات:**
- لیست IP ایران (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- مسیریابی ترافیک داخلی مستقیم (`MIKROTIK_INTERNAL_GATEWAY`)
- مسیریابی ترافیک خارجی از VPN (`MIKROTIK_EXTERNAL_GATEWAY`)

---

## 2. DNS Cache (کش‌کننده DNS)

**هدف:** کاهش وابستگی به DNS خارجی و افزایش سرعت پاسخ‌گویی.

**مزایا:**
- کاهش درخواست‌های DNS به خارج
- افزایش پایداری در صورت قطع DNS
- ذخیره DNS سایت‌های پرکاربرد

**تنظیمات:**
- سرورهای DNS: 1.1.1.1, 8.8.8.8
- حجم کش: 2048KiB
- DNS Static برای google.com, github.com, cloudflare.com

---

## 3. Multi-WAN (مسیریابی چندمسیره)

**هدف:** اتصال به چندین اینترنت (فیبر، ۴G، ۵G) و Failover خودکار.

**مزایا:**
- افزایش پایداری در صورت قطع یک مسیر
- تقسیم بار بین چندین اتصال (PCC)
- کاهش تأثیر قطعی یک ارائه‌دهنده

**تنظیمات:**
- PPPoE Client برای wan1/wan2
- Check Gateway با Ping
- PCC با `per-connection-classifier`

---

## 4. Smart Firewall (فایروال هوشمند)

**هدف:** تشخیص و مسدودسازی حملات DoS و ترافیک مخرب.

**مزایا:**
- محافظت از شبکه در برابر حملات
- مسدودسازی ترافیک مخرب
- شناسایی Port Scan

**تنظیمات:**
- SYN Flood Protection (`connection-limit=10,32`)
- ICMP limit
- PSD (port scan detection)
- لیست سیاه آی‌پی‌ها

---

## 5. Mesh Client (کلاینت Mesh)

**هدف:** اتصال به شبکه‌های محلی برای ارتباطات در قطع کامل.

**مزایا:**
- حفظ ارتباطات محلی در blackout
- اشتراک‌گذاری اینترنت بین کاربران
- هم‌راستا با `phoenix-mesh` در Phoenix Offline

**تنظیمات:**
- SSID: `phoenix-mesh` (env: `MIKROTIK_MESH_SSID`)
- Interface: `wifi1` روی hap ax3
- مسیر 192.168.200.0/24

---

## 6. VPN Server (سرور VPN چندلایه)

**هدف:** پشتیبانی از WireGuard، L2TP/IPSec و OpenVPN.

**مزایا:**
- مدیریت متمرکز کاربران
- سازگاری با کلاینت‌های مختلف
- کلیدها از env (نه hardcode)

**تنظیمات:**
- `MIKROTIK_WG_PRIVATE_KEY`, `MIKROTIK_WG_PUBLIC_KEY`
- `MIKROTIK_L2TP_PSK`
- OpenVPN TCP پورت 1194

---

## 7. Monitoring (مانیتورینگ و گزارش‌گیری)

**هدف:** جمع‌آوری داده‌های ترافیک و ارسال به Phoenix Auto-Adapt.

**مزایا:**
- تحلیل وضعیت ترافیک
- تشخیص اختلالات
- Syslog به `PHOENIX_SYSLOG_HOST`

**تنظیمات:**
- Remote syslog پورت 514
- Graphing interface=all
- Topics: info, error, wireguard, firewall

---

## ترتیب استقرار

```
dns_cache → smart_splitter → multi_wan → smart_firewall → vpn_server → mesh_client → monitoring
```

## دستورات

```bash
# تولید اسکریپت‌ها
PYTHONPATH=src python3 src/main.py mikrotik generate

# استقرار SSH
./deploy/mikrotik_deploy.sh --ip 192.168.88.1 --user admin --password '...'

# استقرار API
PYTHONPATH=src python3 deploy/mikrotik_deploy_winbox.py --ip 192.168.88.1 --username admin --password '...'
```
