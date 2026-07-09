# 🔥 PHOENIX VPN V10 + HARD MODE – COMPLETE MASTER FILE

نسخه نهایی (۱۰ از ۱۰) – مرجع پیاده‌سازی در Cursor.

## دستورالعمل اجرا

1. این فایل در ریشه پروژه ذخیره شده است.
2. در Chat بفرستید:

```
من می‌خواهم پروژه Phoenix VPN را بر اساس این مستند کامل پیاده‌سازی کنم.
ابتدا: orchestrator, protocols, security
سپس: healer, verification, obfuscation, hard_mode, ai
در نهایت: deploy, web panel, tests
خروجی‌ها در ./phoenix-output
پس از اتمام: COMPLETION_REPORT_FINAL.html
```

## ساختار پروژه

```
phoenix-vpn/
├── .env.example
├── quick_setup.sh
├── requirements.txt
├── src/
│   ├── orchestrator/
│   ├── protocols/
│   ├── security/
│   ├── obfuscation/
│   ├── healer/
│   ├── verification/
│   ├── ai/
│   ├── hard_mode/
│   ├── offline/
│   └── monitoring/
├── web/          # Flask panel + auth
├── tests/
├── deploy/
└── docs/
```

## پنل وب

- URL: `http://localhost:5050`
- کاربر پیش‌فرض: `admin` / `phoenix123`
- متغیرها: `PHOENIX_PANEL_PORT`, `SECRET_KEY`, `PHOENIX_PANEL_USER`, `PHOENIX_PANEL_PASSWORD`

## راه‌اندازی سریع

```bash
chmod +x quick_setup.sh
./quick_setup.sh
```

یا:

```bash
pip3 install -r requirements.txt
pip3 install -r web/requirements_web.txt
cp .env.example .env   # ویرایش DOPRAX_API_KEY
PYTHONPATH=src python3 -m pytest tests/ -q
PYTHONPATH=src python3 src/completion_report_final.py
cd web && ./run.sh
```

## چک‌لیست نهایی

- [x] ۶ پروتکل + تونل‌های جایگزین (SSH, ICMP, DoH)
- [x] Obfuscation (SNI, padding, udp2raw, fragmentation, noise)
- [x] Security (Kill Switch, leak checks, Fake-IP)
- [x] Healer (Heartbeat, Fallback, Auto-Healer)
- [x] AI (Filtering Detector, Dynamic Config, Feedback Loop)
- [x] Hard Mode + Offline (Mesh, QR, Emergency)
- [x] پنل با احراز هویت
- [x] تست‌ها و گزارش `COMPLETION_REPORT_FINAL.html`

## وضعیت

**Production-Ready** – Istanbul + Warsaw deployed, DE/FR excluded.

جزئیات بیشتر: `docs/developer_guide.md`, `docs/hard_mode_guide.md`, `PHOENIX_V10_HARD_MODE.md`.
