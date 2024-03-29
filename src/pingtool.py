#!/usr/bin/env python

"""
A simple ping tool. Pings hosts and appends results to stdout and to:

    /tmp/pingtool.csv

"""

import commands
import csv
import datetime
import json
import os
import sys
import time
from argparse import ArgumentParser
from contextlib import contextmanager

from ping import Ping

PING_TIMEOUT = 3000 # this is wifi, people. Could be slow.
PING_HOSTS = ['10.11.0.1', 'google.com']

OSX_AIRPORT_TOOL = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport'

parser = ArgumentParser(description=__doc__.strip())

parser.add_argument(
    'hosts',
    metavar='HOST',
    nargs='*',
    default=PING_HOSTS,
    help='Hosts to ping',
    )

@contextmanager
def no_stdout():
    try:
        with open('/dev/null', 'w') as f:
            sys.stdout = f
            yield
    finally:
        sys.stdout = sys.__stdout__

def get_user():
    if "SUDO_USER" in os.environ:
        return os.environ['SUDO_USER']
    else:
        return os.getlogin()

def utctime():
    """ Return the current ISO 8601 timestamp in UTC. """
    return datetime.datetime.utcnow().isoformat()

def get_osx_ap_info():
    """
    Runs the OS X airport utility tool and returns data on the current
    AP.

         agrCtlRSSI: -84
         agrExtRSSI: 0
        agrCtlNoise: -90
        agrExtNoise: 0
              state: running
            op mode: station
         lastTxRate: 65
            maxRate: 144
    lastAssocStatus: 0
        802.11 auth: open
          link auth: wpa2-psk
              BSSID: 1c:17:d3:17:79:70
               SSID: twilio
                MCS: 7
            channel: 6
    """
    status, output = commands.getstatusoutput(
        '%s -I' % OSX_AIRPORT_TOOL
        )
    chunks = (
        line.split(':', 1) for line in output.splitlines()
        )
    result = dict(
        (k.strip(), v.strip()) for k, v in chunks
        )

    int_keys = ['agrCtlRSSI', 'agrExtRSSI', 'agrCtlNoise', 'agrExtNoise', 'lastTxRate', 'maxRate', 'lastAssocStatus', 'MCS', 'channel']
    for key in int_keys:
        result[key] = int(result[key])
    
    return result

def get_linux_ap_info():
    # do some different stuff here.
    status, output = commands.getstatusoutput("nm-tool|grep -E '\*.*Infra'")
    lines = output.splitlines()
    assert len(lines) == 1
    chunks = lines[0].split(None)
    result = {
        'SSID':  chunks[0][1:-1],
        'BSSID': chunks[2][:-1]
    }
    return result

def get_ap_info():
    """
    Returns a dict of AP info, including (most essentially) these
    two keys:
    
        'SSID': the SSID of the AP
        'BSSID': the BSSID of the AP

    """

    if os.path.exists(OSX_AIRPORT_TOOL):
        return get_osx_ap_info()
    else:
        return get_linux_ap_info()

def ping_host(host):
    with no_stdout():
        p = Ping(host, timeout=PING_TIMEOUT)
        return p.do()

class MultiFile(object):
    def __init__(self, *args):
        self.files = args

    def write(self, data):
        for f in self.files:
            f.write(data)

def main(hosts):
    ap_info = get_ap_info()
    ssid, bssid = ap_info['SSID'], ap_info['BSSID']
    user = get_user()

    with open('/tmp/pingtool.csv', 'a') as f:
        tee = MultiFile(sys.stdout, f)
        tee.write('#%s\n' % json.dumps(ap_info))
        writer = csv.writer(tee)
        writer.writerow(
            ('user', 'ssid', 'bssid', 'utc_time', 'host', 'delay')
            )

        while True:
            for host in hosts:
                delay = ping_host(host)
                writer.writerow(
                    (user, ssid, bssid, utctime(), host, delay)
                    )
            time.sleep(2)

if __name__ == '__main__':
    args = parser.parse_args()
    try:
        main(args.hosts)
    except KeyboardInterrupt:
        pass
