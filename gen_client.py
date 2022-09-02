#!/usr/bin/env python3
import os, os.path
import json
import subprocess
import sys
import ipaddress
import urllib.request

if len(sys.argv) > 0:
    if "help" in sys.argv[1]:
        print("Usage: gen_client.py [client_name] [site-to-site subnet]\n\tEx: gen_client.py RemoteClient 10.0.0.0/24\n\n\tclient_name: The name the client will have (for reference only) - Default is clientX (X is client number)\n\tsite-to-site subnet: The subnet this client has access to for site-to-site configuration. Automatically sets up AllowedIPs for site-to-site connection on FUTURE clients only.")
        exit()


# This script will generate a new __basic__ client for the VPN. There will be no special configuration. It will only contain "common-to-all" configuration, and will need to be modified for special clients.

json_data = {}

# Read network_data.json:
with open("/etc/wireguard/clients/network_data.json", "r") as f:
    json_data = json.loads(f.read())

def gen_keys():
    priv_key = subprocess.check_output("wg genkey", shell=True).rstrip().decode("ASCII")
    pub_key = subprocess.check_output(f"echo {priv_key} | wg pubkey", shell=True).rstrip().decode("ASCII")
    return priv_key, pub_key

# Generate a new client config:

if len(sys.argv) > 2:
    try:
        subnet = ipaddress.IPv4Network(sys.argv[2], strict=True)
    except ValueError:
        print("You didn't provide a valid CIDR notation for subnet...")
        exit()

client_num = json_data["num_clients"]+1
client_subnet = sys.argv[2] if len(sys.argv) > 2 else ""
client_name = sys.argv[1] if len(sys.argv) > 1 else f"client{client_num}"
network = json_data["server_address"].split(".")
client_address = f"{network[0]}.{network[1]}.{network[2]}.{client_num+1}"
client_privkey, client_pubkey = gen_keys()
client_allowedips = json_data["offsite-subnets"]
server_pubkey = f"{json_data['server_pub']}"
server_allowed = f"{client_address}/32"
if client_subnet != "": server_allowed = server_allowed+f",{client_subnet}"


config = (
    f"# {client_name}\n"
    f"[Interface]\n"
    f"Address = {client_address}\n"
    f"PrivateKey = {client_privkey}\n"
    f"\n"
    f"[Peer]\n"
    f"PublicKey = {server_pubkey}\n"
    f"Endpoint = {json_data['server_public']}:{json_data['listen_port']}\n"
    f"AllowedIPs = {json_data['subnet'] if len(client_allowedips) == 0 else json_data['subnet']+','+','.join(client_allowedips)}\n"
    f"PersistentKeepalive = 25\n"
)

server_config = (
    f"\n\n# {client_name}\n"
    f"[Peer]\n"
    f"PublicKey = {client_pubkey}\n"
    f"AllowedIPs = {server_allowed}"
)

client_block = {
    "name": client_name,
    "private_key": client_privkey,
    "public_key": client_pubkey,
    "address": client_address,
    "subnet": client_subnet
}

### Modify json_data:
if client_subnet != "":
    json_data["offsite-subnets"].append(client_subnet)
json_data["clients"].append(client_block)
json_data["num_clients"] += 1

with open("/etc/wireguard/clients/network_data.json", "w") as f:
    json.dump(json_data, f, indent="    ")

with open(f"/etc/wireguard/clients/{client_name}.conf", "w") as f:
    f.write(config)

with open(f"/etc/wireguard/{json_data['server_name']}.conf", "a") as f:
    f.write(server_config)

print(config)
