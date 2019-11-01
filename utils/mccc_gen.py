from moceansdk import McccBuilder, Mccc
from .call_info import CallState, LanguageChoice

def is_digit(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def ivr_init(call):
    """
    Returns MCCC JSON when it first initialised
    """
    record_action = Mccc.record()
    english_say_action = Mccc.say('Welcome to Mocean Voice IVR. For English, please press 1.')
    chinese_say_action = Mccc.say('中文请按二').set_language('cmn-CN')
    collect_action = Mccc.collect(f'http://{call.host}/voice/collect-mccc').set_minimum(1).set_maximum(1).set_timeout(5000)

    mccc = McccBuilder().add(record_action).add(english_say_action).add(chinese_say_action).add(collect_action)
    return mccc.build()

def ivr_get_language(digit, call):
    """
    Returns an mccc object for 2nd phase of IVR
    """

    # Define an mccc builder
    mccc = McccBuilder()
    # Create mccc actions
    english_say_action = Mccc.say('Would you like to listen to some music? Press any key to proceed.')
    chinese_say_action = Mccc.say('你想听听音乐吗？若想，请按任意一键').set_language('cmn-CN')
    english_say_action_proceed = Mccc.say('I would assume you picked English as we did not receive anything.')
    english_say_action_warning = Mccc.say('You did not pressed any valid key, we will end the conversation now.')
    collect_action = Mccc.collect(f'http://{call.host}/voice/collect-mccc').set_minimum(1).set_maximum(1).set_timeout(5000)

    if is_digit(digit):
        # Convert input string into number
        digit = float(digit)
        if digit == 1:
            # Pressed 1 for english
            mccc.add(english_say_action)
            call.set_language(LanguageChoice.LANG_EN_US)
        elif digit == 2:
            # Pressed 2 for chinese
            mccc.add(chinese_say_action)
            call.set_language(LanguageChoice.LANG_CNM_CN)
        else:
            # Invalid input, but we should assume English and proceed
            mccc.add(english_say_action_proceed)
            mccc.add(english_say_action)
            call.set_language(LanguageChoice.LANG_EN_US)
        # Add a collect action for proceeding action
        mccc.add(collect_action)
    else:
        mccc.add(english_say_action_proceed)
        mccc.add(english_say_action)
        call.set_language(LanguageChoice.LANG_EN_US)
        # Add a collect action for proceeding action
        mccc.add(collect_action)
    return mccc

def ivr_play(digit, call):
    mccc = McccBuilder()

    english_reject_say_action = Mccc.say('Ok bye!')
    chinese_reject_say_action = Mccc.say('那再见啦！').set_language('cmn-CN')
    play_action = Mccc.play('https://file-examples.com/wp-content/uploads/2017/11/file_example_MP3_700KB.mp3')

    if digit is not None and len(digit) > 0:
        mccc.add(play_action)
    else:
        if call.language == LanguageChoice.LANG_CNM_CN:
            mccc.add(chinese_reject_say_action)
        else:
            # default to english
            mccc.add(english_reject_say_action)

    return mccc

def ivr_end():
    pass

def ivr_check(digit, call):
    """
    Sends relative MCCC for its respective digits pressed depending on the call state
    """
    if call.state == CallState.CALL_INIT:
        mccc = ivr_get_language(digit, call)
        call.next_state()
    elif call.state == CallState.CALL_OBTAIN_LANGUAGE:
        mccc = ivr_play(digit, call)
        call.next_state()
    elif call.CallState == CallState.CALL_PLAY_FILE:
        mccc = ivr_end()
        call.next_state()

    if mccc is not None:
        return mccc.build()
    else:
        return '[]'

