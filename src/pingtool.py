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

def utctime():
    """ Return the current ISO 8601 timestamp in UTC. """
    return datetime.datetime.utcnow().isoformat()

def get_ap_info():
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
        '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I'
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
    user = os.getlogin()

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
