##
# Handling call state, building mocean commands and returns
##
from moceansdk import McBuilder, Mc
import logging
from .call_info import CallState, LanguageChoice


def is_digit(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def ivr_init(call):
    """
    Returns mocean command JSON when it first initialised
    """
    # Create mocean commands for say action
    record_action = Mc.record()
    english_say_action = Mc.say('Welcome to Mocean Voice IVR. For English, please press 1.').set_barge_in(True)  # nopep8
    chinese_say_action = Mc.say('中文请按二').set_language('cmn-CN').set_barge_in(True)  # nopep8
    # Create mocean command for collect
    collect_action = Mc.collect(f'http://{call.host}/voice/collect-command')
    collect_action.set_minimum(1).set_maximum(1).set_timeout(5000)

    # Adding mocean_command actions into mocean_command
    mocean_command = McBuilder()        # create builder
    mocean_command.add(record_action)   # adding record actions
    mocean_command.add(english_say_action)  # say it in english
    mocean_command.add(chinese_say_action)  # say it in chinese
    mocean_command.add(collect_action)  # adding collect action

    return False, mocean_command.build()


def ivr_get_language(digit, call):
    """
    Returns an Mc object for 2nd phase of IVR
    """

    # Define a mocean command builder
    mocean_command = McBuilder()
    # Create mocean commands for say action
    english_say_action = Mc.say('Would you like to listen to some music? Press any key to proceed.').set_barge_in(True)  # nopep8
    chinese_say_action = Mc.say('你想听听音乐吗？若想，请按任意一键').set_language('cmn-CN').set_barge_in(True)  # nopep8
    english_say_action_proceed = Mc.say('Invalid input, we would assume you have picked English').set_barge_in(True)  # nopep8

    # Cleansing digit cache
    english_say_action.set_clear_digit_cache(True)
    chinese_say_action.set_clear_digit_cache(True)
    english_say_action_proceed.set_clear_digit_cache(True)

    # Create mocean command for collect
    collect_action = Mc.collect(f'http://{call.host}/voice/collect-command')
    collect_action.set_minimum(1).set_maximum(1).set_timeout(5000)
    # set a random character to avoid default '#' character termination
    collect_action.set_terminators('x')

    if is_digit(digit):
        # Convert input string into number
        digit = float(digit)
        if digit == 1:
            # Pressed 1 for english
            mocean_command.add(english_say_action)
            call.set_language(LanguageChoice.LANG_EN_US)
        elif digit == 2:
            # Pressed 2 for chinese
            mocean_command.add(chinese_say_action)
            call.set_language(LanguageChoice.LANG_CNM_CN)
        else:
            # Invalid input, but we should assume English and proceed
            mocean_command.add(english_say_action_proceed)
            mocean_command.add(english_say_action)
            call.set_language(LanguageChoice.LANG_EN_US)
        # Add a collect action for proceeding action
        mocean_command.add(collect_action)
    else:
        mocean_command.add(english_say_action_proceed)
        mocean_command.add(english_say_action)
        call.set_language(LanguageChoice.LANG_EN_US)
        # Add a collect action for proceeding action
        mocean_command.add(collect_action)
    return mocean_command


def ivr_play(digit, call):
    """
    Returns an Mc object for playing an URL file, or saying bye statements
    """
    mocean_command = McBuilder()

    # Create mocean commands for say action
    english_reject_say_action = Mc.say('Ok bye!')
    chinese_reject_say_action = Mc.say('那再见啦！').set_language('cmn-CN')

    # Sample music from downloaded from:
    # http://amachamusic.chagasi.com/music_konekonoosanpo.html
    play_action = Mc.play(f'http://{call.host}/audio/konekonoosanpo.mp3')  # nopep8

    if digit is not None and len(digit) > 0:
        mocean_command.add(play_action)
    else:
        if call.language == LanguageChoice.LANG_CNM_CN:
            mocean_command.add(chinese_reject_say_action)
        else:
            # default to english
            mocean_command.add(english_reject_say_action)

    return mocean_command


def ivr_end(call):
    # Creates empty mocean_command and delete call, this should end
    # the call on Mocean VoiceGW
    logging.error(f'Call state should have ended on CALL_GET_CONSENT, current callstate: {call.state}')  # nopep8
    return McBuilder()


def ivr_check(digit, call):
    """
      Sends relative mocean command for its respective digits pressed
      depending on the call state
    """
    is_del_call = False

    # logging.debug(f'>>>>>>> digit[{digit}]')
    if call.state == CallState.CALL_INIT:
        mocean_command = ivr_get_language(digit, call)
        call.next_state()
    elif call.state == CallState.CALL_OBTAIN_LANGUAGE:
        mocean_command = ivr_play(digit, call)
        call.next_state()
    else:
        mocean_command = ivr_end(call)
        is_del_call = True

    if not is_del_call:
        # Checks if it is the last state, if it is, delete call
        is_del_call = call.is_last_state()
    return is_del_call, mocean_command.build()
