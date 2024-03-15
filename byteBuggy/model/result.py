#!/usr/bin/env python
# -*- coding: utf-8 -*-

# from ..util.color import Color
from ..config import Configuration

import os
import time
from json import loads, dumps

class CrackResult(object):
    ''' Abstract class containing results from a crack session '''

    # File to save cracks to, in PWD
    cracked_file = Configuration.cracked_file

    def __init__(self):
        self.date = int(time.time())
        self.readable_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.date))

    def dump(self):
        raise Exception('Unimplemented method: dump()')

    def to_dict(self):
        raise Exception('Unimplemented method: to_dict()')

    def print_single_line(self, longest_essid):
        raise Exception('Unimplemented method: print_single_line()')

    def print_single_line_prefix(self, longest_essid):
        essid = self.essid if self.essid else 'N/A'
        print(' ')
        print('%s' % essid.ljust(longest_essid))
        print('  ')
        print('%s' % self.bssid.ljust(17))
        print('  ')
        print('%s' % self.readable_date.ljust(19))
        print('  ')

    def save(self):
        ''' Adds this crack result to the cracked file and saves it. '''
        name = CrackResult.cracked_file
        saved_results = []
        if os.path.exists(name):
            with open(name, 'r') as fid:
                text = fid.read()
            try:
                saved_results = loads(text)
            except Exception as e:
                print(' error while loading %s: %s' % (name, str(e)))

        # Check for duplicates
        this_dict = self.to_dict()
        this_dict.pop('date')
        for entry in saved_results:
            this_dict['date'] = entry.get('date')
            if entry == this_dict:
                # Skip if we already saved this BSSID+ESSID+TYPE+KEY
                print(' %s already exists in %s, skipping.' % (
                    self.essid, Configuration.cracked_file))
                return

        saved_results.append(self.to_dict())
        with open(name, 'w') as fid:
            fid.write(dumps(saved_results, indent=2))
        print(' saved crack result to %s (%d total)'
            % (name, len(saved_results)))

    @classmethod
    def display(cls):
        ''' Show cracked targets from cracked file '''
        name = cls.cracked_file
        if not os.path.exists(name):
            print(' file %s not found' % name)
            return

        with open(name, 'r') as fid:
            cracked_targets = loads(fid.read())

        if len(cracked_targets) == 0:
            print(' no results found in %s' % name)
            return

        print('\n Displaying %d cracked target(s) from %s\n' % (
            len(cracked_targets), name))

        results = sorted([cls.load(item) for item in cracked_targets], key=lambda x: x.date, reverse=True)
        longest_essid = max([len(result.essid or 'ESSID') for result in results])

        # Header
        print(' ')
        print('ESSID'.ljust(longest_essid))
        print('  ')
        print('BSSID'.ljust(17))
        print('  ')
        print('DATE'.ljust(19))
        print('  ')
        print('TYPE'.ljust(5))
        print('  ')
        print('KEY')
        print('')
        print(' ' + '-' * (longest_essid + 17 + 19 + 5 + 11 + 12))
        print('')
        # Results
        for result in results:
            result.print_single_line(longest_essid)
        print('')


    @classmethod
    def load_all(cls):
        if not os.path.exists(cls.cracked_file): return []
        with open(cls.cracked_file, 'r') as json_file:
            json = loads(json_file.read())
        return json

    @staticmethod
    def load(json):
        ''' Returns an instance of the appropriate object given a json instance '''
        if json['type'] == 'WPA':
            from .wpa_result import CrackResultWPA
            result = CrackResultWPA(json['bssid'],
                                    json['essid'],
                                    json['handshake_file'],
                                    json['key'])
        elif json['type'] == 'WEP':
            from .wep_result import CrackResultWEP
            result = CrackResultWEP(json['bssid'],
                                    json['essid'],
                                    json['hex_key'],
                                    json['ascii_key'])

        # elif json['type'] == 'WPS':
        #     from .wps_result import CrackResultWPS
        #     result = CrackResultWPS(json['bssid'],
        #                             json['essid'],
        #                             json['pin'],
        #                             json['psk'])

        elif json['type'] == 'PMKID':
            from .pmkid_result import CrackResultPMKID
            result = CrackResultPMKID(json['bssid'],
                                      json['essid'],
                                      json['pmkid_file'],
                                      json['key'])
        result.date = json['date']
        result.readable_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(result.date))
        return result

if __name__ == '__main__':
    # Deserialize WPA object
    print('\nCracked WPA:')
    json = loads('{"bssid": "AA:BB:CC:DD:EE:FF", "essid": "Test Router", "key": "Key", "date": 1433402428, "handshake_file": "hs/capfile.cap", "type": "WPA"}')
    obj = CrackResult.load(json)
    obj.dump()

    # Deserialize WEP object
    print('\nCracked WEP:')
    json = loads('{"bssid": "AA:BB:CC:DD:EE:FF", "hex_key": "00:01:02:03:04", "ascii_key": "abcde", "essid": "Test Router", "date": 1433402915, "type": "WEP"}')
    obj = CrackResult.load(json)
    obj.dump()

    # # Deserialize WPS object
    # print('\nCracked WPS:')
    # json = loads('{"psk": "the psk", "bssid": "AA:BB:CC:DD:EE:FF", "pin": "01234567", "essid": "Test Router", "date": 1433403278, "type": "WPS"}')
    # obj = CrackResult.load(json)
    # obj.dump()
