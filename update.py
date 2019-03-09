#!/usr/bin/env python3
"""Script for CI update. """

import argparse
import base64
import json
import os
import subprocess
from datetime import datetime
from itertools import chain
from typing import List

from gfwlist2acl import ChinaTimezone, get_acl_rules

DOWNLOAD_URL = 'https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt'

__dirname__ = os.path.abspath(os.path.dirname(__file__))


def _file_path(*other):
    return os.path.join(__dirname__, *other)


HASH_FILE = _file_path('hash.txt')


def download() -> List[str]:
    """Download gfwlist

    Returns:
        List[str]
    """

    return (base64.b64decode(
        subprocess.run(['curl', DOWNLOAD_URL],
                       encoding='utf-8',
                       stdout=subprocess.PIPE,
                       check=True).stdout)
            .decode('utf-8'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--release', action='store_true',
                        help='create new release if repository data is not up to date')

    args = parser.parse_args()
    is_release = args.release

    now = datetime.now(ChinaTimezone())
    blacklist, whitelist = (get_acl_rules(download().splitlines()))

    common_header = ['# Home: https://github.com/NateScarlet/gfwlist.acl',
                     '# Date: {}'.format(now.isoformat())]
    with open(_file_path('gfwlist.acl'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(chain(
            ['#'],
            common_header,
            ['# URL: https://raw.githubusercontent.com/'
             'NateScarlet/gfwlist.acl/master/gfwlist.acl',
             '#',
             '',
             '[bypass_all]',
             '',
             '[proxy_list]',
             '', ],
            blacklist,
            ['', '[bypass_list]', ''],
            whitelist,
            [''])))
    with open(_file_path('gfwlist.white.acl'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(chain(
            ['#'],
            common_header,
            ['# URL: https://raw.githubusercontent.com/'
             'NateScarlet/gfwlist.acl/master/gfwlist.white.acl',
             '#',
             '',
             '[proxy_all]',
             '',
             '[proxy_list]',
             '', ],
            blacklist,
            ['', '[bypass_list]', ''],
            whitelist,
            [''])))
    with open(_file_path('gfwlist.acl.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'blacklist': blacklist,
                   'whitelist': whitelist},
                  f,
                  indent=4,)

    if not is_release:
        print('Updated repository data, skip release since not specified `--release`')
        return

    subprocess.run(['git', 'add', 'gfwlist.acl',
                    'gfwlist.white.acl', 'gfwlist.acl.json'], check=True)
    diff = subprocess.run(['git', 'diff', '--cached', 'gfwlist.acl.json'],
                          encoding='utf-8',
                          stdout=subprocess.PIPE,
                          check=True).stdout
    if not diff:
        print('Already up to date')
        return
    subprocess.run(
        ['git', 'commit', '-m', 'update acl files [skip ci]\n\n'+diff], check=True)
    subprocess.run(['git', 'tag', now.strftime('%Y.%m.%d')], check=True)
    subprocess.run(['git', 'push'], check=True)
    subprocess.run(['git', 'push', '--tags'], check=True)


if __name__ == '__main__':
    main()
