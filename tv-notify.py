#!/usr/bin/python3

from subprocess import Popen, PIPE
from time import sleep, strptime, strftime
from datetime import datetime
import json


blank_schema = {
        "account": "",
        "peers": {},
        "subscribers": []
    }

class Peer:
    def __init__(self):
        self.name = ""
        self.ip = ""
        self.pubkey = ""
        self.endpoints = []
        self.last_hs = 500
        self.new_hs = 0
        self.enabled = True

    def __str__(self):
        string = (
                f"Peer {self.name}\n"
                f"- Pubkey: {self.pubkey}\n"
                f"- IP: {self.ip}\n"
                f"- Endpoints: {self.endpoints}\n"
                f"- Last Handshake: {self.last_hs}\n"
                f"- New Handshake: {self.new_hs}"
            )
        return string

def send_text(message):
    for sub in tv_data["subscribers"]:
        print(f"[*] Sending message to {sub}.")
        cli = Popen(["signal-cli", "-u", "+19103154725", "send", "-m", message, sub], stdout=PIPE)
        wg_data_output = "".join(cli.communicate()[0].decode('UTF-8'))
        print(wg_data_output)

def sig_rec():
    cli = Popen(["signal-cli", "-u", "+19103154725", "receive"], stdout=PIPE)
    wg_data_output = "".join(cli.communicate()[0].decode('UTF-8'))

def get_wg_data():
    # scrapes wg command and converts to our peer schema
    wg_data = Popen(["wg"], stdout=PIPE)
    wg_data_output = "".join(wg_data.communicate()[0].decode('UTF-8')).split("\n\n")
    for section in wg_data_output: # A section is either a "interface" or "peer" block.
        if section[:4] == "peer": # This is confirmed as a peer block.
            pub = section.split("\n")[0].split(": ")[1]
            if pub not in peers:
                peer = Peer()
            else:
                peer = peers[pub]
            for line in section.split("\n"):
                peer.pubkey = pub
                for client in client_data["clients"]:
                    if client["public_key"] == peer.pubkey:
                        peer.name = client["name"]
                        peer.ip = client["address"]
                if "endpoint" in line:
                    endpoint = line.split(": ")[1]
                    if endpoint.split(":")[0] not in peer.endpoints: peer.endpoints.append(endpoint.split(":")[0])
                if "handshake" in line:
                    peer.new_hs = process_time(line)
            peers[pub] = peer

def process_time(hs_line):
    hs = 0
    time_data = [1,60,3600,86400]
    tme = hs_line.split(": ")[1]
    last_hs = [0,0,0,0]
    for i,t in enumerate(tme.split(",")[::-1]):
        last_hs[i] = ''.join(filter(str.isdigit, t))
        hs += int(last_hs[i])*time_data[i]
    return hs

def notify():
    for pub in peers:
        peer = peers[pub]
        if peer.last_hs > 300:
            if peer.new_hs < 120:
                if peer.enabled:                        
                        send_text(f"Notification: Client {peer.name} has connected at {peer.ip} from [{peer.endpoints[-1]}].")
        peer.last_hs = peer.new_hs

def fill_peers():
    jsonPeers = {}
    for sub in peers:
        peer = peers[sub]
        jsonPeers[sub] = {
                "name": peer.name,
                "address": peer.ip,
                "pubkey": peer.pubkey,
                "endpoints": peer.endpoints,
                "last_hs": peer.last_hs,
                "enabled": peer.enabled
            }
    return jsonPeers

if __name__ == "__main__":
    try:
        with open('/etc/wireguard/clients/network_data.json',"r") as f:
            client_data = json.load(f)
    except FileNotFoundError as e:
        print(f"network_data.json file not found! Ensure you are using with network generator.", file=sys.stderr)
        exit()
    try:
        with open('/etc/wireguard/clients/tv_data.json',"r") as a:
            tv_data = json.load(a)
    except FileNotFoundError as e:
        print(f"Data file not found! Creating a blank one. Please fill it out (/etc/wireguard/clients/tv_data.json)", file=sys.stderr)
        with open('/etc/wireguard/clients/tv_data.json',"w") as a:
            json.dump(blank_schema, a, indent="")
        exit()

    peers = {} # Temp in-memory reference of data on disk.
    for pub in tv_data["peers"]:
        peer = tv_data["peers"][pub]
        obj = Peer()
        obj.pubkey = peer["pubkey"]
        obj.name = peer["name"]
        obj.ip = peer["address"]
        obj.endpoints = peer["endpoints"]
        obj.last_hs = peer["last_hs"]
        obj.enabled = peer['enabled']
        peers[peer["pubkey"]] = obj
        

    get_wg_data()
    notify()
    tv_data["peers"] = fill_peers()
    with open('/etc/wireguard/clients/tv_data.json',"w") as a:
        json.dump(tv_data, a, indent="    ")
    sig_rec()    
