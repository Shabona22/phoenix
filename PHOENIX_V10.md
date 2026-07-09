# 🔥 PHOENIX VPN V10 – MASTER EXECUTION FILE FOR CURSOR PRO
## سیستم مقاوم در برابر سانسور پیشرفته – نسخه نهایی صنعتی

---

## ⚠️ دستورالعمل اجرا در Cursor Pro

1. این فایل را به‌عنوان `PHOENIX_V10.md` در پروژه‌ی Cursor ذخیره کن.
2. Cursor را باز کن و این فایل را باز کن.
3. در پنجره‌ی Chat، این دستور را بفرست:

```
من می‌خواهم پروژه Phoenix VPN را بر اساس این مستند کامل پیاده‌سازی کنم.
لطفاً تمام مراحل را به‌صورت گام‌به‌گام و با رعایت اولویت‌های زیر اجرا کن:
ابتدا: فایل‌های اصلی (orchestrator, protocols, security)
سپس: ماژول‌های حیاتی (healer, verification, obfuscation)
در نهایت: اسکریپت‌های استقرار و تست‌ها
استفاده از هیچ مدل خارجی (Llama و غیره) ممنوع است. فقط از قابلیت‌های داخلی Cursor استفاده کن.
همه خروجی‌ها را در پوشه‌ی ./phoenix-output ذخیره کن.
پس از اتمام، یک فایل COMPLETION_REPORT.html تولید کن.
```

---

## 📂 ساختار نهایی پروژه (همه فایل‌ها)

```
phoenix-vpn/
├── src/
│   ├── orchestrator/
│   │   ├── node_manager.py
│   │   ├── config_generator.py
│   │   ├── subscription_manager.py
│   │   └── api_client.py (Doprax)
│   ├── protocols/
│   │   ├── base.py
│   │   ├── xray_config.py
│   │   ├── shadowsocks_config.py
│   │   ├── wireguard_config.py
│   │   ├── openvpn_config.py # با Obfsproxy + tls-crypt
│   │   ├── l2tp_config.py # با IKEv1 + NAT-T
│   │   └── hysteria_config.py
│   ├── security/
│   │   ├── kill_switch.py
│   │   ├── dns_leak_check.py
│   │   ├── ip_leak_check.py
│   │   ├── webrtc_leak_check.py
│   │   └── tls_fingerprint.py
│   ├── obfuscation/
│   │   ├── sni_rotator.py
│   │   ├── padding.py
│   │   ├── jitter.py
│   │   ├── port_rotator.py
│   │   ├── keepalive_engine.py
│   │   └── behavioral_morphing.py
│   ├── healer/
│   │   ├── heartbeat.py
│   │   ├── fallback_manager.py
│   │   └── dos_detector.py
│   ├── verification/
│   │   └── user_traffic_validator.py
│   ├── routing/
│   │   └── pac_generator.py
│   ├── initializer/
│   │   └── bootstrap_embedded.py
│   ├── offline/
│   │   ├── qr_backup.py
│   │   └── mesh_connector.py
│   ├── protocols/
│   │   └── udp_over_tcp.py
│   └── utils/
│       ├── time_keeper.py
│       ├── log_manager.py
│       ├── budget_alert.py
│       └── crypto.py
├── tests/
│   ├── unit/
│   │   ├── test_openvpn_l2tp.py
│   │   ├── test_security.py
│   │   └── test_obfuscation.py
│   └── integration/
│       ├── test_orchestrator.py
│       └── test_simulator.py
├── deploy/
│   ├── docker-compose.yml
│   ├── bootstrap.sh
│   └── health_check.sh
└── docs/
    ├── architecture.md
    ├── future_proofing.md
    └── user_guide.md
```

---

## 🧩 کدهای کلیدی (قابل کپی در Cursor)

### ۱. `src/protocols/openvpn_config.py`

```python
import secrets
from typing import Dict, Any
from .base import ProtocolBase

class OpenVPNConfig(ProtocolBase):
    def __init__(self):
        super().__init__("OpenVPN", "2.6")
        self.obfs_methods = ["obfs4", "obfs3"]
        self.ciphers = ["AES-256-GCM", "CHACHA20-POLY1305"]
        
    def generate_config(self, server_ip: str, port: int = None, **kwargs) -> Dict[str, Any]:
        if not port:
            port = self._generate_random_port(8000, 65000)
        return {
            "protocol": "openvpn",
            "server": {"ip": server_ip, "port": port, "proto": "tcp"},
            "cryptography": {
                "cipher": "AES-256-GCM",
                "auth": "SHA256",
                "tls_version": "1.3",
                "tls_crypt_v2": True
            },
            "obfuscation": {
                "enabled": True,
                "method": "obfs4",
                "param": secrets.token_hex(16)
            },
            "auth": {
                "username": kwargs.get("username", self._generate_password(12)),
                "password": kwargs.get("password", self._generate_password(20))
            }
        }
    
    def generate_client_config(self, config: Dict[str, Any]) -> str:
        return f"""
client
dev tun
proto tcp
remote {config['server']['ip']} {config['server']['port']}
cipher AES-256-GCM
auth SHA256
tls-version-min 1.3
tls-crypt-v2
obfsproxy obfs4 127.0.0.1:1080
<ca>
{config.get('ca_cert', '')}
</ca>
"""
```

### ۲. `src/protocols/l2tp_config.py`

```python
import secrets
from typing import Dict, Any
from .base import ProtocolBase

class L2TPConfig(ProtocolBase):
    def __init__(self):
        super().__init__("L2TP/IPSec", "1.0")
        
    def generate_config(self, server_ip: str, psk: str = None, **kwargs) -> Dict[str, Any]:
        if not psk:
            psk = secrets.token_hex(20)
        return {
            "protocol": "l2tp_ipsec",
            "server": {"ip": server_ip, "ipsec_port": 4500, "l2tp_port": 1701},
            "ipsec": {
                "phase1": {"algorithm": "aes256-sha256-modp2048", "lifetime": "28800s"},
                "phase2": {"algorithm": "aes256-sha256", "lifetime": "3600s"},
                "pre_shared_key": psk,
                "nat_traversal": True
            },
            "auth": {
                "username": kwargs.get("username", f"user_{secrets.token_hex(4)}"),
                "password": kwargs.get("password", self._generate_password(16))
            }
        }
    
    def generate_client_config(self, config: Dict[str, Any]) -> str:
        return f"""
L2TP/IPSec PSK
Server: {config['server']['ip']}
PSK: {config['ipsec']['pre_shared_key']}
Username: {config['auth']['username']}
Password: {config['auth']['password']}
NAT Traversal: Enabled
"""
```

### ۳. `src/verification/user_traffic_validator.py` (ماژول خودمختار)

```python
import requests
import time
import threading
from src.healer.fallback_manager import FallbackManager

class TrafficValidator:
    def __init__(self, fallback_manager: FallbackManager):
        self.fallback = fallback_manager
        self.test_endpoints = [
            "https://1.1.1.1/cdn-cgi/trace",
            "https://api.ipify.org?format=json"
        ]
        self.failure_count = 0
        self.max_failures = 3
        self.is_running = False
    
    def start(self):
        self.is_running = True
        threading.Thread(target=self._loop, daemon=True).start()
    
    def _loop(self):
        while self.is_running:
            if not self._check():
                self.failure_count += 1
                if self.failure_count >= self.max_failures:
                    self._trigger_fallback()
                    self.failure_count = 0
            else:
                self.failure_count = 0
            time.sleep(30)
    
    def _check(self) -> bool:
        proxy = {"http": "socks5://127.0.0.1:1080", "https": "socks5://127.0.0.1:1080"}
        for endpoint in self.test_endpoints:
            try:
                if requests.get(endpoint, proxies=proxy, timeout=5).status_code == 200:
                    return True
            except:
                continue
        return False
    
    def _trigger_fallback(self):
        if not self.fallback.switch_protocol():
            if not self.fallback.switch_node():
                self.fallback.emergency_mode()
```

---

## ⚙️ تنظیمات خاص Cursor Pro (قبل از اجرا)

| تنظیمات | مقدار | توضیح |
|---------|-------|-------|
| Model | GPT-4 یا Claude 3.5 Sonnet | برای تسک‌های معماری و امنیتی |
| Max Tokens | 4096 | کافی برای تولید فایل‌های کامل |
| Temperature | 0.3 | برای خروجی دقیق و قابل اعتماد |
| Enable Codebase Context | ✅ فعال | تا Cursor ساختار پروژه را بهتر درک کند |
| Auto-run Tests | ✅ فعال | برای تأیید خودکار خروجی‌ها |

---

من به عنوان مدیر شبکه، این فایل را به‌عنوان آخرین نسخه‌ی نهایی تأیید می‌کنم.

**ویژگی‌های کلیدی نسخه V10:**

- ✅ همه ۶ پروتکل با پیکربندی‌های عبور از فیلترینگ ۱۴۰۴
- ✅ سیستم خودترمیمی کامل (بدون نیاز به مدیر)
- ✅ تأیید واقعی عبور ترافیک (نه فقط Heartbeat)
- ✅ مقاومت در برابر DPI هوش مصنوعی و مسدودسازی UDP
- ✅ پشتیبانی از حالت قطع کامل اینترنت (QR/Bluetooth)
- ✅ حذف کامل وابستگی به Llama و سرویس‌های خارجی
- ✅ بهینه‌سازی برای Cursor Pro با مصرف توکن هوشمند
