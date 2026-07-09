# PHOENIX VPN V10 – HARD MODE READY

سیستم مقاوم در برابر سانسور پیشرفته — نسخه نهایی صنعتی + شرایط سخت (Hard Mode).

این مستند مکمل `PHOENIX_V10.md` است و فقط لایه‌های «شرایط سخت» را توصیف می‌کند. هسته‌ی V10
(شش پروتکل، orchestrator، امنیت، خودترمیمی، استقرار) از قبل پیاده و روی سرورهای فعال مستقر شده است.

---

## هدف Hard Mode

وقتی روش‌های عادی دورزدن فیلترینگ شکست می‌خورند (DPI تهاجمی، مسدودسازی مبتنی بر ML/LLM،
یا قطع کامل اینترنت)، این لایه‌ها به‌عنوان «آخرین خط دفاع» فعال می‌شوند:

1. **SSH / ICMP Tunneling** — آخرین کانال‌های عبور وقتی همه پروتکل‌های اصلی مسدودند.
2. **Content Simulator** — شکل‌دهی ترافیک شبیه سرویس‌های پرکاربرد برای فریب طبقه‌بندهای ML/LLM.
3. **LLM Defender** — امتیازدهی «طبیعی بودن» ترافیک و تطبیق خودکار الگو.
4. **Mesh / P2P** — تبادل کانفیگ در شبکه محلی هنگام قطع کامل اینترنت.
5. **Personal Server Manager** — رجیستری سرورهای شخصی کاربر (خارج از Doprax) به‌عنوان پشتیبان.
6. **Emergency Fallback** — زنجیره‌ی تصمیم‌گیری برای انتخاب آخرین راه فعال.

> همه‌ی خروجی‌ها در `./phoenix-output` نوشته می‌شوند. هیچ مدل خارجی (Llama و غیره) استفاده نمی‌شود؛
> فقط منطق داخلی پایتون.

---

## ساختار ماژول‌های Hard Mode

```
src/
├── protocols/
│   ├── ssh_tunnel.py            # تونل SOCKS از طریق SSH (آخرین راه)
│   └── icmp_tunnel.py           # تونل ICMP (پشتیبان SSH)
├── obfuscation/
│   └── content_simulator.py     # شبیه‌سازی محتوای واقعی برای فریب DPI/LLM
├── offline/
│   └── mesh_connector.py        # MeshP2P: کشف همسایه و تبادل کانفیگ محلی
└── hard_mode/
    ├── __init__.py              # HardMode facade + وضعیت آمادگی
    ├── personal_server_manager.py
    ├── llm_defender.py
    └── emergency_fallback.py
tests/unit/test_hard_mode.py
docs/hard_mode_guide.md
```

---

## قراردادهای طراحی

- هیچ ماژولی در `__init__` سوکت واقعی باز نمی‌کند یا به شبکه وصل نمی‌شود؛ عملیات شبکه صریح و
  با فراخوانی متد فعال می‌شود (قابل تست بدون root و بدون شبکه).
- هر ماژول یک `generate_config() -> dict` دارد که در گزارش و باندل استقرار قابل استفاده است.
- وابستگی‌های اختیاری (`paramiko`) به‌صورت lazy import می‌شوند تا نبودشان کل سیستم را نشکند.

---

## نحوه استفاده

```python
from hard_mode import HardMode

hm = HardMode()
report = hm.readiness()          # وضعیت آمادگی همه لایه‌ها
cfg = hm.generate_config()       # کانفیگ کامل Hard Mode برای phoenix-output
plan = hm.emergency_plan(        # انتخاب آخرین راه بر اساس شرایط
    dpi_blocking=True, internet_down=False,
)
```

تولید گزارش:

```bash
PYTHONPATH=src python3 src/hard_mode_report.py
# → phoenix-output/COMPLETION_REPORT_HARD_MODE.html
```

---

## چک‌لیست Hard Mode

- [x] SSH Tunneling (آخرین راه)
- [x] ICMP Tunneling (پشتیبان SSH)
- [x] Content Simulator (فریب DPI/LLM)
- [x] LLM Defender (امتیاز طبیعی بودن + تطبیق)
- [x] Mesh / P2P (قطع کامل اینترنت)
- [x] Personal Server Manager (سرورهای شخصی)
- [x] Emergency Fallback (زنجیره تصمیم)
- [x] تست واحد `test_hard_mode.py`
- [x] مستند `docs/hard_mode_guide.md`
- [x] گزارش `COMPLETION_REPORT_HARD_MODE.html`
