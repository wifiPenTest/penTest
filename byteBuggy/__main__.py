#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from .config import Configuration
except (ValueError, ImportError) as e:
    raise Exception('You may need to run byteBuggy from the root directory (which includes README.md)', e)

from .util.color import Color

import os
import sys


class ByteBuggy(object):

    def __init__(self):
        '''
        Initializes byteBuggy. Checks for root permissions and ensures dependencies are installed.
        '''

        self.print_banner()

        Configuration.initialize(load_interface=False)

        if os.getuid() != 0:
            print(' error: byteBuggy must be run as root')
            print(' re-run with sudo')
            Configuration.exit_gracefully(0)

        from .tools.dependency import Dependency
        Dependency.run_dependency_check()


    def start(self):
        '''
        Starts target-scan + attack loop, or launches utilities dpeending on user input.
        '''
        from .model.result import CrackResult
        from .model.handshake import Handshake
        from .util.crack import CrackHelper

        if Configuration.show_cracked:
            CrackResult.display()

        elif Configuration.check_handshake:
            Handshake.check()

        elif Configuration.crack_handshake:
            CrackHelper.run()

        else:
            Configuration.get_monitor_mode_interface()
            self.scan_and_attack()


    def print_banner(self):
        print('''
                ___.            __        __________                           
\_ |__ ___.__._/  |_  ____\______   \__ __  ____   ____ ___.__.
 | __ <   |  |\   __\/ __ \|    |  _/  |  \/ ___\ / ___<   |  |
 | \_\ \___  | |  | \  ___/|    |   \  |  / /_/  > /_/  >___  |
 |___  / ____| |__|  \___  >______  /____/\___  /\___  // ____|
     \/\/                \/       \/     /_____//_____/ \/     
        
              ''')


    def scan_and_attack(self):
        '''
        1) Scans for targets, asks user to select targets
        2) Attacks each target
        '''
        from .util.scanner import Scanner
        from .attack.all import AttackAll

        print('')

        # Scan
        s = Scanner()
        targets = s.select_targets()

        # Attack
        attacked_targets = AttackAll.attack_multiple(targets)

        print('Finished attacking %d target(s), exiting' % attacked_targets)


##############################################################


def entry_point():
    try:
        byteBuggy = ByteBuggy()
        byteBuggy.start()
    except Exception as e:
        Color.pexception(e)
        print('\n Exiting\n')

    except KeyboardInterrupt:
        print('\n Interrupted, Shutting down...')

    Configuration.exit_gracefully(0)


if __name__ == '__main__':
    entry_point()
