###### This program will read switch IP addresses listed in text file "SW_list.txt" ######
########### only CRC errors of connected trunk ports are collected and stored  ###########
######### script runs every 24 hours and removes CRC logs after it is finished ###########

import re #-------------------------Regex fin item helper
import time 
import warnings
import paramiko  
import logging.handlers
from cryptography.utils import CryptographyDeprecationWarning
from progress.bar import Bar
with warnings.catch_warnings():
    warnings.filterwarnings('ignore', category=CryptographyDeprecationWarning)
     
username = '[Username_to_ssh]'
password = 'Passwd'
syslogSRV = '[SYSLOG_SRV_IP]'
sw_file = "SWITCH_List_FIle_PATH"
switchList = []
result= []
incorrectPass = ''
failedConnect = ''

def sshCommand(cmd):
    client.connect(host, username=username, password=password)
    _stdin, _stdout, _stderr = client.exec_command(cmd)
    return (_stdout.read().decode())
def findTrunks():
    trunkList = []
    cmdOutput = sshCommand("show int statu | i trunk")
    res = [i.start() for i in re.finditer('/0/', cmdOutput)]
    for x in res:
        trunkList.append(cmdOutput[x-3:x+5])
    return trunkList
def findHostName():
    cmdOutput = sshCommand("show run | i hostname")
    res = [i.start() for i in re.finditer('hostname ', cmdOutput)]
    hostname = cmdOutput[res[0]+9:len(cmdOutput)]
    return hostname
def clearCounters(interface):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host , port=22, username=username, password=password)
    connection = ssh.invoke_shell()
    connection.send(f"clear counters {interface}\n")
    time.sleep(1)
    connection.send("\n")

#opens TXT file in program path
with open(sw_file) as file: 
    switchList = file.read().splitlines()
    
#creates progress bar 
bar = Bar(f'Checking switches for CRC error in progress:  ', max=len(switchList))
startTime = time.time()

for host in switchList:
    try:
        client = paramiko.client.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=username, password=password)

        # find and adds trunk port names to list
        trunk = findTrunks()
        # counts CRC errors per trunk port and adds to total number of CRC errors
        totalCRC = 0
        for i in trunk:
            text1 = sshCommand(f"show interfaces {i} | include input errors, [^0 CRC]")
            end = [i.start() for i in re.finditer(' CRC', text1)]
            begin = [i.start() for i in re.finditer('input errors, ', text1)]
            if end != []:
                intCRC = text1[begin[0]+14:end[0]+1]
                totalCRC += int(intCRC)
                clearCounters(i)  # clears counters for selected trunk port
        hostname = findHostName()
        if totalCRC > 10 :
            result.append([hostname.rstrip(),host,totalCRC])
        bar.next()
        client.close()
        
    except paramiko.AuthenticationException:
        #print("Incorrect password")
        incorrectPass += (host + ' _ ') 
        break
    except:
        bar.next()
        failedConnect += (host + ' _ ')
        #print("Something Went Wrong")
bar.finish()


#Sorts result by larger CRC error
lst = sorted(result, key=lambda x: x[2], reverse=True)
logMessage = ''
#Create a syslog message with all stored crc logs
for x in lst :
    logMessage += f'{x[0]}  ,   {x[1]}  ,   {x[2]}\n'
mkaLogger = logging.getLogger('mkaMontior')
mkaLogger.setLevel(logging.INFO)
handler = logging.handlers.SysLogHandler(address = (syslogSRV,514))
mkaLogger.addHandler(handler)

if incorrectPass != '' or failedConnect !='':
    logMessage += 'Connection to the following Switches failed\n'
if incorrectPass != '' :
    logMessage += '\nReason incorrect password : ' + incorrectPass
if failedConnect != '' :
    logMessage += '\nReason Other: ' + failedConnect

mkaLogger.info(logMessage)

