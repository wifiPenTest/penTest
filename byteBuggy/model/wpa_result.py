#!/usr/bin/env python
# -*- coding: utf-8 -*-

# from ..util.color import Color
from .result import CrackResult

class CrackResultWPA(CrackResult):
    def __init__(self, bssid, essid, handshake_file, key):
        self.result_type = 'WPA'
        self.bssid = bssid
        self.essid = essid
        self.handshake_file = handshake_file
        self.key = key
        super(CrackResultWPA, self).__init__()

    def dump(self):
        if self.essid:
            print(' %s: %s' %
                ('Access Point Name'.rjust(19), self.essid))
        if self.bssid:
            print(' %s: %s' %
                ('Access Point BSSID'.rjust(19), self.bssid))
        print(' %s: %s' %
            ('Encryption'.rjust(19), self.result_type))
        if self.handshake_file:
            print(' %s: %s' %
                ('Handshake File'.rjust(19), self.handshake_file))
        if self.key:
            print(' %s: %s' % ('PSK (password)'.rjust(19), self.key))
        else:
            print(' %s  key unknown' % ''.rjust(19))

    def print_single_line(self, longest_essid):
        self.print_single_line_prefix(longest_essid)
        print('%s' % 'WPA'.ljust(5))
        print('  ')
        print('Key: %s' % self.key)
        print('')

    def to_dict(self):
        return {
            'type'  : self.result_type,
            'date'  : self.date,
            'essid' : self.essid,
            'bssid' : self.bssid,
            'key'   : self.key,
            'handshake_file' : self.handshake_file
        }

if __name__ == '__main__':
    w = CrackResultWPA('AA:BB:CC:DD:EE:FF', 'Test Router', 'hs/capfile.cap', 'abcd1234')
    w.dump()

    w = CrackResultWPA('AA:BB:CC:DD:EE:FF', 'Test Router', 'hs/capfile.cap', 'Key')
    print('\n')
    w.dump()
    w.save()
    print(w.__dict__['bssid'])

