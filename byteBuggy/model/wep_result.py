#!/usr/bin/env python
# -*- coding: utf-8 -*-

# from ..util.color import Color
from .result import CrackResult

import time

class CrackResultWEP(CrackResult):
    def __init__(self, bssid, essid, hex_key, ascii_key):
        self.result_type = 'WEP'
        self.bssid     = bssid
        self.essid     = essid
        self.hex_key   = hex_key
        self.ascii_key = ascii_key
        super(CrackResultWEP, self).__init__()

    def dump(self):
        if self.essid:
            print('      ESSID: %s' % self.essid)
        print('      BSSID: %s' % self.bssid)
        print(' Encryption: %s' % self.result_type)
        print('    Hex Key: %s' % self.hex_key)
        if self.ascii_key:
            print('  Ascii Key: %s' % self.ascii_key)

    def print_single_line(self, longest_essid):
        self.print_single_line_prefix(longest_essid)
        print('%s' % 'WEP'.ljust(5))
        print('  ')
        print('Hex: %s' % self.hex_key.replace(':', ''))
        if self.ascii_key:
            print(' (ASCII: %s)' % self.ascii_key)
        print('')

    def to_dict(self):
        return {
            'type'      : self.result_type,
            'date'      : self.date,
            'essid'     : self.essid,
            'bssid'     : self.bssid,
            'hex_key'   : self.hex_key,
            'ascii_key' : self.ascii_key
        }

if __name__ == '__main__':
    crw = CrackResultWEP('AA:BB:CC:DD:EE:FF', 'Test Router', '00:01:02:03:04', 'abcde')
    crw.dump()
    crw.save()

