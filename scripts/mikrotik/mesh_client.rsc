# Mesh Client
# Phoenix V10 MikroTik Ready – hap_ax3
:log info "phoenix: applying Mesh Client"
# hap ax3 uses wifiwave2; interface name may be wifi1
:do { /interface wifi set [find default-name=wifi1] disabled=no ssid="phoenix-mesh" } on-error={}
:do { /ip route add dst-address=192.168.200.0/24 gateway=wifi1 comment=phoenix-mesh-route } on-error={}
:do { /system logging add topics=wireless action=memory } on-error={}
:log info "phoenix: mesh_client done"
