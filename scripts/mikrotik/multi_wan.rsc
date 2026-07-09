# Multi-WAN
# Phoenix V10 MikroTik Ready – hap_ax3
:log info "phoenix: applying Multi-WAN"
:do { /interface pppoe-client add interface=ether1 user=user1 password=pass1 name=wan1 disabled=no } on-error={}
:do { /interface pppoe-client add interface=ether2 user=user2 password=pass2 name=wan2 disabled=no } on-error={}
:do { /ip route add gateway=wan1 check-gateway=ping distance=1 comment=phoenix-wan1 } on-error={}
:do { /ip route add gateway=wan2 check-gateway=ping distance=2 comment=phoenix-wan2 } on-error={}
:do { /ip firewall mangle add chain=prerouting dst-address-type=!local in-interface=bridge action=mark-connection new-connection-mark=wan1-conn per-connection-classifier=src-address-and-port:2/0 passthrough=yes comment=phoenix-pcc-wan1 } on-error={}
:do { /ip firewall mangle add chain=prerouting dst-address-type=!local in-interface=bridge action=mark-connection new-connection-mark=wan2-conn per-connection-classifier=src-address-and-port:2/1 passthrough=yes comment=phoenix-pcc-wan2 } on-error={}
:do { /ip route add gateway=192.168.1.1 routing-mark=wan1-conn comment=phoenix-wan1-pcc } on-error={}
:do { /ip route add gateway=192.168.2.1 routing-mark=wan2-conn comment=phoenix-wan2-pcc } on-error={}
:do { /system logging add topics=firewall action=memory } on-error={}
:log info "phoenix: multi_wan done"
