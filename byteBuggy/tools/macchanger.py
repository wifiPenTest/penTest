#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .dependency import Dependency
from ..tools.ifconfig import Ifconfig
from ..util.color import Color

class Macchanger(Dependency):
    dependency_required = False
    dependency_name = 'macchanger'
    dependency_url = 'apt-get install macchanger'

    is_changed = False

    @classmethod
    def down_macch_up(cls, iface, options):
        '''Put interface down, run macchanger with options, put interface up'''
        from ..util.process import Process

        Color.clear_entire_line()
        print('\r macchanger: taking interface %s down...' % iface)

        Ifconfig.down(iface)

        Color.clear_entire_line()
        print('\r macchanger: changing mac address of interface %s...' % iface)

        command = ['macchanger']
        command.extend(options)
        command.append(iface)
        macch = Process(command)
        macch.wait()
        if macch.poll() != 0:
            print('\n macchanger: error running %s' % ' '.join(command))
            print(' output: %s, %s' % (macch.stdout(), macch.stderr()))
            return False

        Color.clear_entire_line()
        print('\r macchanger: bringing interface %s up...' % iface)

        Ifconfig.up(iface)

        return True


    @classmethod
    def get_interface(cls):
        # Helper method to get interface from configuration
        from ..config import Configuration
        return Configuration.interface


    @classmethod
    def reset(cls):
        iface = cls.get_interface()
        print('\r macchanger: resetting mac address on %s...' % iface)
        # -p to reset to permanent MAC address
        if cls.down_macch_up(iface, ['-p']):
            new_mac = Ifconfig.get_mac(iface)

            Color.clear_entire_line()
            print('\r macchanger: reset mac address back to %s on %s' % (new_mac, iface))


    @classmethod
    def random(cls):
        from ..util.process import Process
        if not Process.exists('macchanger'):
            print(' macchanger: not installed')
            return

        iface = cls.get_interface()
        print('\n macchanger: changing mac address on %s' % iface)

        # -r to use random MAC address
        # -e to keep vendor bytes the same
        if cls.down_macch_up(iface, ['-e']):
            cls.is_changed = True
            new_mac = Ifconfig.get_mac(iface)

            Color.clear_entire_line()
            print('\r macchanger: changed mac address to %s on %s' % (new_mac, iface))


    @classmethod
    def reset_if_changed(cls):
        if cls.is_changed:
            cls.reset()

