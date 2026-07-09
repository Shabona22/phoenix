# Monitoring
# Phoenix V10 MikroTik Ready – hap_ax3
:log info "phoenix: applying Monitoring"
:do { /system logging action add name=phoenix target=remote remote=192.168.88.10 port=514 } on-error={}
:do { /system logging add topics=info action=phoenix } on-error={}
:do { /system logging add topics=error action=phoenix } on-error={}
:do { /system logging add topics=wireguard action=phoenix } on-error={}
:do { /system logging add topics=firewall action=phoenix } on-error={}
:do { /tool graphing interface add interface=all } on-error={}
:log info "phoenix: monitoring done"
