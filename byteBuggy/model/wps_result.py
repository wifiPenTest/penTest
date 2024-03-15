#!/usr/bin/env python
# -*- coding: utf-8 -*-

# from ..util.color import Color
from ..model.result import CrackResult

import time

class CrackResultWPS(CrackResult):
    def __init__(self, bssid, essid, pin, psk):
        self.result_type = 'WPS'
        self.bssid = bssid
        self.essid = essid
        self.pin   = pin
        self.psk   = psk
        super(CrackResultWPS, self).__init__()

    def dump(self):
        if self.essid is not None:
            print(' %s: %s' % (      'ESSID'.rjust(12), self.essid))
        if self.psk is None:
            psk = 'N/A'
        else:
            psk = '%s' % self.psk
        print(' %s: %s'     % (      'BSSID'.rjust(12), self.bssid))
        print(' %s: WPA (WPS)' % 'Encryption'.rjust(12))
        print(' %s: %s'     % (     'WPS PIN'.rjust(12), self.pin))
        print(' %s: %s'     % ('PSK/Password'.rjust(12), psk))

    def print_single_line(self, longest_essid):
        self.print_single_line_prefix(longest_essid)
        print('%s' % 'WPS'.ljust(5))
        print('  ')
        if self.psk:
            print('Key: %s ' % self.psk)
        print('PIN: %s' % self.pin)
        print('')

    def to_dict(self):
        return {
            'type'  : self.result_type,
            'date'  : self.date,
            'essid' : self.essid,
            'bssid' : self.bssid,
            'pin'   : self.pin,
            'psk'   : self.psk
        }

if __name__ == '__main__':
    crw = CrackResultWPS('AA:BB:CC:DD:EE:FF', 'Test Router', '01234567', 'the psk')
    crw.dump()
    crw.save()

