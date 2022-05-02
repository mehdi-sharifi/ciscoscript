from netmiko import ConnectHandler
import json

#Dictionary for store session information
device = {"device_type": "cisco_ios", "ip": "x.x.x.x", "username": "your_username", "password": "your_password", "port": 22, "secret": "Enable_password"}
#establish ssh connection to the target
ssh_connection = ConnectHandler(**device)
#run a command and store result int a variable
result = ssh_connection.send_command('show interfaces gigabitEthernet 1/0/49 | include Ethernet|CRC|input errors|output errors')
#print result of commant in terminal
print(device["ip"], result)
