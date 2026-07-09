# Phoenix VPN V10 – MikroTik Ready (Final)

سیستم مقاوم در برابر سانسور با پشتیبانی کامل از MikroTik hap ax3.

## ساختار پروژه (در phoenix-vpn)

```
src/mikrotik/
├── advanced_config_generator.py
├── usb_manager.py
├── winbox_connector.py
└── deploy_winbox.py

scripts/mikrotik/
├── smart_splitter.rsc
├── dns_cache.rsc
├── multi_wan.rsc
├── smart_firewall.rsc
├── mesh_client.rsc
├── vpn_server.rsc
└── monitoring.rsc

deploy/
├── mikrotik_deploy.sh          # SSH primary
└── mikrotik_deploy_winbox.py   # RouterOS API secondary

docs/
├── mikrotik_advanced_roles.md
├── mikrotik_usb_guide.md
└── mikrotik_winbox_setup.md

phoenix-output/MIKROTIK_DEPLOYMENT_REPORT.html
```

## دستورات سریع

```bash
# تولید اسکریپت‌ها
PYTHONPATH=src python3 src/main.py mikrotik generate

# گزارش HTML
PYTHONPATH=src python3 src/mikrotik_deployment_report.py

# استقرار SSH
./deploy/mikrotik_deploy.sh --generate-only
./deploy/mikrotik_deploy.sh --ip 192.168.88.1 --user admin --password 'PASS'

# استقرار API
PYTHONPATH=src python3 deploy/mikrotik_deploy_winbox.py --ip 192.168.88.1 --username admin --password 'PASS'
```

## متغیرهای محیطی

| متغیر | توضیح |
|---|---|
| `PHOENIX_SYSLOG_HOST` | مقصد syslog برای Auto-Adapt |
| `MIKROTIK_WG_PRIVATE_KEY` | کلید WireGuard |
| `MIKROTIK_WG_PUBLIC_KEY` | کلید عمومی peer |
| `MIKROTIK_L2TP_PSK` | PSK برای L2TP |
| `PHOENIX_MIKROTIK_CONFIG` | مسیر JSON تنظیمات |

## ترتیب استقرار

`dns_cache` → `smart_splitter` → `multi_wan` → `smart_firewall` → `vpn_server` → `mesh_client` → `monitoring`

## یکپارچگی Phoenix

- **Auto-Adapt:** `monitoring.rsc` ارسال syslog به `PHOENIX_SYSLOG_HOST`
- **Offline Mesh:** SSID `phoenix-mesh` هم‌راستا با `src/offline/mesh_connector.py`
- **Fallback:** روتر به‌عنوان gateway محلی برای split tunneling

## تست‌ها

```bash
pytest tests/unit/test_mikrotik*.py -q
```

## مستندات

- [نقش‌های پیشرفته](docs/mikrotik_advanced_roles.md)
- [راهنمای USB](docs/mikrotik_usb_guide.md)
- [راهنمای WinBox/API](docs/mikrotik_winbox_setup.md)
