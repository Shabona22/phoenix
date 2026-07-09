# Smart Firewall
# Phoenix V10 MikroTik Ready – hap_ax3
:log info "phoenix: applying Smart Firewall"
:do { /ip firewall filter add chain=input protocol=tcp tcp-flags=syn connection-limit=10,32 action=drop comment=phoenix-syn-flood } on-error={}
:do { /ip firewall filter add chain=input protocol=icmp icmp-options=8:0 limit=5,5 action=accept comment=phoenix-icmp-limit } on-error={}
:do { /ip firewall filter add chain=input protocol=tcp psd=21,3s,3,1 action=drop comment=phoenix-port-scan } on-error={}
:do { /ip firewall address-list add list=blacklist address=1.2.3.4 comment=phoenix-blacklist-example } on-error={}
:do { /ip firewall filter add chain=input src-address-list=blacklist action=drop comment=phoenix-blacklist-drop } on-error={}
:do { /system logging add topics=firewall action=memory } on-error={}
:log info "phoenix: smart_firewall done"
