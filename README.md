#### This is eventually going to have some good details about this repo.

Components:

​	o generate_vpn_network.py :: This script is a guided walkthrough that will setup your initial wireguard server. Run this first, it creates it's own data on disk that the rest of these scripts will utilize. 

​	o gen_client.py :: This script is used to generate a client configuration and update the server / json automatically. It is capable of generating a site-to-site configuration, but ALL site-to-site configs need to be created FIRST. Creating a normal "client" peer config before a site-to-site will mean that peer won't have access to that other network. This script will output ONLY the config so you should redirect stdout to your desired config file. This makes it easy to run over ssh as so: `ssh user@server /root/gen_client.py > client.conf`

​	o generate_qr.sh :: Pass the client.conf you want to generate a QR code for and it will spit it out in the terminal.

​	o InstallSignalEN.py :: Untested, but it's supposed to install and setup the signal-cli.

 	o tv-notify.py :: This script will generate a configuration file in /etc/wireguard/clients/ that you can add a signal account to (that is already setup in signal-cli) and a few "subscribers" to (other signal phone numbers with country code) and every time the script runs it will check send a signal message to notify if a client has connected. I set it up on a cronjob to run every minute or so and it works fine. 