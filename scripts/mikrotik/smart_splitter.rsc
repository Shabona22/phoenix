# Smart Splitter
# Phoenix V10 MikroTik Ready – hap_ax3
:log info "phoenix: applying Smart Splitter"
:do { /ip firewall address-list add list=Iran_IPs address=10.0.0.0/8 } on-error={}
:do { /ip firewall address-list add list=Iran_IPs address=172.16.0.0/12 } on-error={}
:do { /ip firewall address-list add list=Iran_IPs address=192.168.0.0/16 } on-error={}
:do { /ip firewall mangle add chain=prerouting dst-address-list=Iran_IPs action=mark-routing new-routing-mark=internal passthrough=yes comment=phoenix-internal } on-error={}
:do { /ip firewall mangle add chain=prerouting dst-address-list=!Iran_IPs action=mark-routing new-routing-mark=external passthrough=yes comment=phoenix-external } on-error={}
:do { /ip route add routing-mark=internal gateway=192.168.1.1 comment=phoenix-internal-route } on-error={}
:do { /ip route add routing-mark=external gateway=wg-server comment=phoenix-external-route } on-error={}
:do { /system logging add topics=firewall action=memory } on-error={}
:log info "phoenix: smart_splitter done"
