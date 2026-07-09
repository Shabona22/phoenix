# MikroTik USB Guide – hap ax3

راهنمای استفاده از مموری فلش USB برای استقرار آفلاین Phoenix.

## پیش‌نیازها

- MikroTik hap ax3 با RouterOS v7
- فلش USB فرمت‌شده (FAT32 توصیه می‌شود)
- پورت USB در پشت دستگاه

## مسیرهای mount

| مسیر | توضیح |
|---|---|
| `/usb1` | ریشه فلش |
| `/usb1/phoenix` | پوشه اسکریپت‌های Phoenix |
| `/disk1/phoenix` | مسیر جایگزین در برخی نسخه‌ها |

## تولید دستورات export

```bash
PYTHONPATH=src python3 -c "
from mikrotik.usb_manager import UsbManager
from pathlib import Path
mgr = UsbManager()
print(mgr.export_scripts_to_usb('scripts/mikrotik'))
"
```

## پشتیبان‌گیری

```bash
PYTHONPATH=src python3 -c "
from mikrotik.usb_manager import UsbManager
print(UsbManager().generate_usb_backup_script())
"
```

خروجی شامل:
- `/system backup save`
- کپی `.backup` به USB
- `/export file=` برای کانفیگ متنی

## استقرار آفلاین از USB

1. اسکریپت‌ها را با `mikrotik generate` بسازید
2. فایل‌های `.rsc` را روی فلش کپی کنید
3. فلش را به روتر وصل کنید
4. در WinBox یا SSH:

```
/import file-name=usb1/phoenix/dns_cache.rsc
/import file-name=usb1/phoenix/smart_splitter.rsc
...
```

## نکات امنیتی

- کلیدهای WireGuard و L2TP PSK را روی USB ذخیره نکنید
- از env vars در زمان تولید اسکریپت استفاده کنید
- پس از استقرار، فلش را جدا کنید

## عیب‌یابی

| مشکل | راه‌حل |
|---|---|
| `/usb1` not found | فلش را دوباره وصل کنید؛ `/system resource print` |
| import failed | syntax را با `/import verbose` بررسی کنید |
| فضای ناکافی | فایل‌های قدیمی backup را حذف کنید |
