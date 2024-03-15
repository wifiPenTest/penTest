#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .wep import AttackWEP
from .wpa import AttackWPA
# from .wps import AttackWPS
# from .pmkid import AttackPMKID
from ..config import Configuration
from ..util.color import Color

class AttackAll(object):

    @classmethod
    def attack_multiple(cls, targets):
        '''
        Attacks all given `targets` (list[byteBuggy.model.target]) until user interruption.
        Returns: Number of targets that were attacked (int)
        '''
        # if any(t.wps for t in targets):
        #     # Warn that WPS attacks are not available.
        #     print(' Note: WPS attacks are not possible because you do not have reaver nor bully')

        attacked_targets = 0
        targets_remaining = len(targets)
        for index, target in enumerate(targets, start=1):
            attacked_targets += 1
            targets_remaining -= 1

            bssid = target.bssid
            essid = target.essid if target.essid_known else 'ESSID unknown'

            print('\n (%d/%d)' % (index, len(targets)) +
                     ' Starting attacks against %s (%s)' % (bssid, essid))

            should_continue = cls.attack_single(target, targets_remaining)
            if not should_continue:
                break

        return attacked_targets

    @classmethod
    def attack_single(cls, target, targets_remaining):
        '''
        Attacks a single `target` (byteBuggy.model.target).
        Returns: True if attacks should continue, False otherwise.
        '''

        attacks = []

        if Configuration.use_eviltwin:
            # TODO: EvilTwin attack
            pass

        elif 'WEP' in target.encryption:
            attacks.append(AttackWEP(target))

        elif 'WPA' in target.encryption:
            # WPA can have multiple attack vectors:

            # # WPS
            # if not Configuration.use_pmkid_only:
            #     if target.wps != False and AttackWPS.can_attack_wps():
            #         # Pixie-Dust
            #         if Configuration.wps_pixie:
            #             attacks.append(AttackWPS(target, pixie_dust=True))

            #         # PIN attack
            #         if Configuration.wps_pin:
            #             attacks.append(AttackWPS(target, pixie_dust=False))

            # if not Configuration.wps_only:
            #     # PMKID
            #     attacks.append(AttackPMKID(target))

                # Handshake capture
                if not Configuration.use_pmkid_only:
                    attacks.append(AttackWPA(target))

        if len(attacks) == 0:
            print(' Error: Unable to attack: no attacks available')
            return True  # Keep attacking other targets (skip)

        while len(attacks) > 0:
            attack = attacks.pop(0)
            try:
                result = attack.run()
                if result:
                    break  # Attack was successful, stop other attacks.
            except Exception as e:
                Color.pexception(e)
                continue
            except KeyboardInterrupt:
                print('\n Interrupted\n')
                answer = cls.user_wants_to_continue(targets_remaining, len(attacks))
                if answer is True:
                    continue  # Keep attacking the same target (continue)
                elif answer is None:
                    return True  # Keep attacking other targets (skip)
                else:
                    return False  # Stop all attacks (exit)

        if attack.success:
            attack.crack_result.save()

        return True  # Keep attacking other targets


    @classmethod
    def user_wants_to_continue(cls, targets_remaining, attacks_remaining=0):
        '''
        Asks user if attacks should continue onto other targets
        Returns:
            True if user wants to continue, False otherwise.
        '''
        if attacks_remaining == 0 and targets_remaining == 0:
            return  # No targets or attacksleft, drop out

        prompt_list = []
        if attacks_remaining > 0:
            prompt_list.append(print('%d attack(s)' % attacks_remaining))
        if targets_remaining > 0:
            prompt_list.append(print('%d target(s)' % targets_remaining))
        prompt = ' and '.join(prompt_list) + ' remain'
        print(' %s' % prompt)

        prompt = ' Do you want to'
        options = '('

        if attacks_remaining > 0:
            prompt += ' continue attacking,'
            options += 'C, '

        if targets_remaining > 0:
            prompt += ' skip to the next target,'
            options += 's, '

        options += 'e)'
        prompt += ' or exit %s? ' % options

        from ..util.input import raw_input
        answer = raw_input(print(prompt)).lower()

        if answer.startswith('s'):
            return None  # Skip
        elif answer.startswith('e'):
            return False  # Exit
        else:
            return True  # Continue

