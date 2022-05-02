from netmiko import ConnectHandler
import json
device = {"device_type": "cisco_ios", "ip": "x.x.x.x", "username": "your_username", "password": "your_password", "port": 22, "secret": "Enable_password"}
ssh_connection = ConnectHandler(**device)
result = ssh_connection.send_command('show interfaces gigabitEthernet 1/0/49 | include Ethernet|CRC|input errors|output errors')
print(device["ip"], result)
