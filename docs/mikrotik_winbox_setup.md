# MikroTik WinBox / API Setup

راهنمای اتصال Phoenix به MikroTik hap ax3.

## تفاوت WinBox GUI و RouterOS API

| پروتکل | پورت | کاربرد |
|---|---|---|
| WinBox GUI | 8291 | رابط گرافیکی (پروتکل اختصاصی) |
| RouterOS API | 8728 | اتوماسیون Phoenix (`WinBoxConnector`) |
| SSH | 22 | استقرار اصلی (`mikrotik_deploy.sh`) |

کلاس `WinBoxConnector` در Phoenix از **RouterOS API (8728)** استفاده می‌کند، نه پروتکل باینری WinBox.

## فعال‌سازی RouterOS API

در WinBox یا SSH:

```
/ip service set api address=192.168.88.0/24 disabled=no port=8728
/ip service print
```

برای دسترسی از LAN:

```
/ip firewall filter add chain=input protocol=tcp dst-port=8728 src-address=192.168.88.0/24 action=accept place-before=0
```

## فعال‌سازی SSH

```
/ip service set ssh disabled=no port=22
/ip service print where name=ssh
```

## استقرار SSH (توصیه‌شده)

```bash
# macOS
brew install sshpass

./deploy/mikrotik_deploy.sh --generate-only   # فقط تولید
./deploy/mikrotik_deploy.sh --ip 192.168.88.1 --user admin --password 'YOUR_PASS'
```

## استقرار API (ثانویه)

```bash
PYTHONPATH=src python3 deploy/mikrotik_deploy_winbox.py \
  --ip 192.168.88.1 \
  --username admin \
  --password 'YOUR_PASS' \
  --port 8728
```

## متغیرهای محیطی

| متغیر | پیش‌فرض | توضیح |
|---|---|---|
| `PHOENIX_SYSLOG_HOST` | 192.168.88.10 | مقصد syslog |
| `MIKROTIK_WG_PRIVATE_KEY` | — | کلید WireGuard سرور |
| `MIKROTIK_WG_PUBLIC_KEY` | — | کلید عمومی peer |
| `MIKROTIK_L2TP_PSK` | — | Pre-shared key L2TP |
| `PHOENIX_MIKROTIK_CONFIG` | — | مسیر JSON تنظیمات |

## تأیید استقرار

```
/log print where message~"phoenix"
/interface wireguard print
/system script print
```

## امنیت

- API و SSH را فقط از subnet مدیریت باز کنید
- کاربر admin جدا با رمز قوی
- پس از استقرار، پورت API را محدود کنید
