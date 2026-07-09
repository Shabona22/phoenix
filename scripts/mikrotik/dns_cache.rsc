# DNS Cache
# Phoenix V10 MikroTik Ready – hap_ax3
:log info "phoenix: applying DNS Cache"
/ip dns set servers=1.1.1.1,8.8.8.8 allow-remote-requests=yes cache-size=2048KiB
/ip dns cache flush
:do { /ip dns static add name=google.com address=142.250.185.78 } on-error={}
:do { /ip dns static add name=github.com address=140.82.121.3 } on-error={}
:do { /ip dns static add name=cloudflare.com address=104.16.124.96 } on-error={}
:do { /system logging add topics=dns action=memory } on-error={}
:log info "phoenix: dns_cache done"
