#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: expandtab ts=4 sts=4 sw=4

import subprocess
import urllib.request
import json
import os
import argparse

VERSION = ''
CURL_VERSION = ''
UA_URL = ''

big = {
    'centos': '/7/isos/x86_64/CentOS-7-x86_64-Everything-2009.iso',
    'centos-vault': '/6.0/isos/x86_64/CentOS-6.0-x86_64-LiveDVD.iso',
    'opensuse': '/distribution/leap/15.5/iso/openSUSE-Leap-15.5-DVD-x86_64-Media.iso',
    'ubuntu-releases': '/22.04/ubuntu-22.04.3-desktop-amd64.iso',
    'debian-cd': '/current/amd64/iso-bd/debian-edu-12.1.0-amd64-BD-1.iso',
    'kali-images': '/kali-2023.2/kali-linux-2023.2-live-amd64.iso',
    'CTAN': '/systems/texlive/Images/texlive.iso',
    'blackarch': '/iso/blackarch-linux-full-2023.04.01-x86_64.iso',
    'archlinux': '/iso/latest/archlinux-x86_64.iso',
    'ubuntu': '/indices/md5sums.gz',
    'debian': '/ls-lR.gz',
}

# filled by CI
mirrors = []

map = {}
res = {}

def check_curl():
    global CURL_VERSION
    try:
        res = subprocess.run(['curl', '--version'], stdout=subprocess.PIPE)
        out = res.stdout.decode('utf-8')
        CURL_VERSION = out.split()[1]
        print(out)
        return 0
    except:
        print("No curl found!")
        return -1

def site_info(url):
    user_agent = 'oh-my-mirrorz/%s (+https://github.com/mirrorz-org/oh-my-mirrorz) %s %s' % (VERSION, UA_URL, "urllib/" + urllib.request.__version__)
    headers = {
        'User-Agent': user_agent
    }

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode('utf-8'))


def speed_test(url, args):
    opt = '-qs'
    if args.ipv4:
        opt += '4'
    elif args.ipv6:
        opt += '6'
    res = subprocess.run(['curl', opt, '-o', os.devnull, '-w', '%{http_code} %{speed_download}',
                          '-m'+str(args.time), '-A', 'oh-my-mirrorz/%s (+https://github.com/mirrorz-org/oh-my-mirrorz) %s curl/%s' % (VERSION, UA_URL, CURL_VERSION), url], stdout=subprocess.PIPE)
    code, speed = res.stdout.decode('utf-8').split()
    return int(code), float(speed)

def human_readable_speed(speed):
    scale = ['B/s', 'KiB/s', 'MiB/s', 'GiB/s', 'TiB/s']
    i = 0
    while (speed > 1024.0):
        i += 1
        speed /= 1024.0
    return f'{speed:.2f} {scale[i]}'

def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-4", "--ipv4", help="IPv4 only when speed testing", action="store_true")
    group.add_argument("-6", "--ipv6", help="IPv6 only when speed testing", action="store_true")
    parser.add_argument("-t", "--time", type=int, default=5, choices=[3, 5, 10, 30, 60], help="Duration of a speed test for one mirror (default: %(default)d)")
    args = parser.parse_args()

    if check_curl() != 0:
        exit(-1)
    for url in mirrors:
        try:
            map[url] = site_info(url)
            print('Loaded', map[url]['site']['abbr'], ':', map[url]['site']['url'])
        except:
            print('! Failed to load', url)
            pass

    print() # one empty line to separate metadata and speedtest

    for _, v in map.items():
        uri_list = []
        if 'big' in v['site']:
            uri_list.append(v['site']['big'])
        for r, u in big.items():
            for m in v['mirrors']:
                if m['cname'] == r:
                    uri_list.append(m['url'] + u)
        if len(uri_list) == 0:
            print('! No big file found for', v['site']['abbr'], v['site']['url'])
            continue

        for uri in uri_list:
            res[v['site']['abbr']] = 0
            print('Speed testing', v['site']['abbr'], uri if uri.startswith("http") else v['site']['url'] + uri, '... ', end='', flush=True)
            code, speed = speed_test(v['site']['url'] + uri, args)
            if code != 200:
                print('HTTP Code', code, 'Speed', human_readable_speed(speed))
            else:
                print(human_readable_speed(speed))
                res[v['site']['abbr']] = speed
                break

    print() # one empty line to separate speedtest and result

    print('RANK', 'ABBR', 'SPEED', sep='\t\t')
    for i, (k, v) in enumerate(sorted(res.items(), key = lambda x: x[1], reverse=True)):
        print(f'{i:02d}:', k, human_readable_speed(v), sep='\t\t')

if __name__ == '__main__':
    main()
