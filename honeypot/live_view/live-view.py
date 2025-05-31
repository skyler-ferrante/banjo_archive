#!/bin/python3

import json
import sys
import signal

#Taken from Blender build script
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

#No annoying output that messes stuff up
def signal_handler(sig, frame):
    print()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

for line in sys.stdin:
    data = json.loads(line)
    if "eventid" in data:
        eventid = data["eventid"]
        if eventid == "cowrie.client.version" or eventid == "cowrie.client.kex":
            continue
        print(bcolors.OKBLUE+data["src_ip"], bcolors.ENDC, eventid, sep="\t", end="\t")
        if eventid == "cowrie.login.failed":
            print(bcolors.FAIL, data["username"]+","+data["password"], bcolors.ENDC, sep="\t", end="")
        elif eventid == "cowrie.login.success":
            print(bcolors.OKBLUE, data["username"]+","+data["password"], bcolors.ENDC, sep="\t", end="")
        elif eventid == "cowrie.command.input":
            print(bcolors.OKGREEN, data["input"], bcolors.ENDC, sep="\t", end="")
        elif eventid == "cowrie.session.file_download":
            if "message" in data:
                print(bcolors.HEADER,data["message"], bcolors.ENDC)
        elif eventid == "cowrie.session.file_upload":
            if "message" in data:
                print(bcolors.HEADER,data["message"], bcolors.ENDC)
        elif eventid == "cowrie.log.closed":
            if data["duplicate"]:
                print(bcolors.HEADER, end="")
            else:
                print(bcolors.WARNING, end="")
            print(str(data["duplicate"])+bcolors.ENDC, end="")
        print()
