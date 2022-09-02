#!/usr/bin/env python3
import json
import ipaddress
import apt
import subprocess
import os
import urllib

network_data = {
    "num_clients": 0,
    "server_pub": "",
    "server_address": "", 
    "listen_port": 51820,
    "offsite-subnets": [], 
    "clients": []
}

def gen_keys():
    priv_key = subprocess.check_output("wg genkey", shell=True).rstrip().decode("ASCII")
    pub_key = subprocess.check_output(f"echo {priv_key} | wg pubkey", shell=True).rstrip().decode("ASCII")
    return priv_key, pub_key

def check_wg():
    cache = apt.Cache()
    cache.open()
    try:
        cache['wireguard'].is_installed
    except KeyError:
        print("Wireguard not installed. Please install with 'sudo apt install wireguard'")
        exit()

print("This script will generate a complex wireguard network capable of several site-to-site nodes as well as several independ access nodes.")
print()
print()
print("We will walk you through the process by asking one question at a time, but you can expect this:")
print(" 1) Establish the static peer (server) on this machine.")
print(" 2) Identify site-to-site nodes - These will be used to link two networks together.")
print(" 3) Generate access peers - This will be used to get access to the wireguard network")
print("                            independent of any site-to-site peers.")
print()
print()
print(" Let's begin:")
check_wg()
os.system("mkdir -p /etc/wireguard/clients")
print()
print("We need to establish the wireguard network")
while(True):
    
    server_name = input("Please name your network [wg0]: ")
    if server_name == "": 
        server_name = "wg0"
    else:
        server_name = server_name.replace(" ","_")

    while(True):
        network = input("Please enter subnet to use (eg: 10.8.0.0/24): ")
        try:
            addr = ipaddress.IPv4Network(network)
            break
        except ValueError:
            print("Not a valid network...")
            pass

    while(True):
        server_port = input("Please enter desired listening port (1023-49151): ")
        if int(server_port) > 1023 and int(server_port) < 49151:
            break

    external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8') 

    subnet = addr
    server_host = str(list(addr.hosts())[0])
    server_priv, server_pub = gen_keys()
    network_data["server_name"] = server_name
    network_data["server_address"] = server_host
    network_data["subnet"] = network
    network_data["server_pub"] = server_pub
    network_data["listen_port"] = server_port
    network_data["server_public"] = external_ip

    server_config = (
        f"# {server_name}\n"
        f"[Interface]\n"
        f"Address = {server_host}\n"
        f"PrivateKey = {server_priv}\n"
        f"ListenPort = {server_port}\n"
        f"# Endpoint IP = {network_data['server_public']}:{network_data['listen_port']}"
    )

    print("This is our current server information:")
    print(server_config)
    print()
    print()
    correct = False
    while(True):
        q = input("Is this correct? (y/n): ")
        if q.lower() == "y":
            correct = True
        break
    if correct == True:
        break

# Server config complete. Let's write it.

with open(f"/etc/wireguard/{server_name}.conf", "w") as f:
    f.write(server_config)

with open(f"/etc/wireguard/clients/network_data.json", "w") as f:
    json.dump(network_data, f, indent="    ")


