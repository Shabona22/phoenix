# VPN Server
# Phoenix V10 MikroTik Ready – hap_ax3
:log info "phoenix: applying VPN Server"
:do { /interface wireguard add name=wg-server private-key="REPLACE_WG_PRIVATE_KEY" comment=phoenix-wg } on-error={}
:do { /ip address add address=10.0.0.1/24 interface=wg-server } on-error={}
:do { /interface wireguard peers add interface=wg-server public-key="REPLACE_WG_PUBLIC_KEY" allowed-address=10.0.0.2/32 comment=phoenix-wg-peer } on-error={}
:do { /ppp profile add name=l2tp-profile local-address=192.168.100.1 remote-address=192.168.100.2-192.168.100.254 } on-error={}
/interface l2tp-server server set enabled=yes default-profile=l2tp-profile
/ip ipsec proposal set [ find default=yes ] enc-algorithms=aes-256-cbc
:do { /ip ipsec peer add address=0.0.0.0/0 passive=yes } on-error={}
:do { /ip ipsec identity add peer=0.0.0.0/0 auth-method=pre-shared-key secret="REPLACE_L2TP_PSK" } on-error={}
/interface ovpn-server server set enabled=yes port=1194 mode=tcp
:do { /system logging add topics=wireguard action=memory } on-error={}
:log info "phoenix: vpn_server done"
