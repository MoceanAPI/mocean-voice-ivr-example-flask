import logging

from flask import Flask, Response, request, jsonify, send_from_directory
from utils.mccc_gen import ivr_init, ivr_check
from utils.call_info import Call

logging.basicConfig(format='[%(asctime)s] - %(message)s', level=logging.DEBUG)
app = Flask(__name__)

calls = {}
call_ended = []


def invalid_response():
    """
      Wrapper for returning invalid response
    """
    return Response(
        '{"error": "Invalid request"}',
        status=400,
        mimetype='application/json'
        )


@app.route('/audio/<path:path>', methods=['GET'])
def get_audio(path):
    """
      Serving static files from audio/ folder
    """
    return send_from_directory('audio', path)


@app.route('/voice/collect-command', methods=['POST'])
def collect_mccc():
    """
      Route received when using `collect` parameters from our MoceanVoice GW
    """
    if 'mocean-call-uuid' not in request.form:
        return invalid_response()

    session_uuid = request.form.get('mocean-session-uuid')
    call_uuid = request.form.get('mocean-call-uuid')
    digits = request.form.get('mocean-digits')
    logging.info(f'### Collect MCCC received from [{call_uuid}] ###')
    host = request.headers['Host']

    if call_uuid not in calls:
        call = Call(session_uuid, call_uuid, None, None, host)
        calls[call_uuid] = call
        logging.debug(f'call-uuid[{call_uuid}] added into calls dict')
        return jsonify(ivr_init(call))
    elif call_uuid in call_ended:
        # If the call has ended but still requesting collect-mccc,
        # it is unprocessable
        return Response('[]', status=422, mimetype='application/json')
    else:
        call = calls[call_uuid]
        del_call, res = ivr_check(digits, call)
        if del_call:
            logging.debug(f'Deleting call-uuid[{call_uuid}] from calls dict')
            del calls[call_uuid]
            call_ended.append(call_uuid)
        return jsonify(res)


@app.route('/voice/inbound-command', methods=['POST'])
def inbound_mccc():
    """
      Route received when an inbound call is received from our MoceanVoice GW
    """

    if 'mocean-call-uuid' not in request.form:
        return invalid_response()

    session_uuid = request.form.get('mocean-session-uuid')
    call_uuid = request.form.get('mocean-call-uuid')
    destination = request.form.get('mocean-to')
    source = request.form.get('mocean-from')

    logging.info(f'### Call received from [{source}], assigned call-uuid[{call_uuid}] ###')  # nopep8
    host = request.headers['Host']

    if call_uuid in calls:
        logging.warning(f'call-uuid[{call_uuid}] is in calls, should use `voice/collect-mccc\' path')  # nopep8
        call = calls[call_uuid]
    elif call_uuid in call_ended:
        # If the call has ended but still requesting inbound-mccc,
        # it is unprocessable
        return Response('[]', status=422, mimetype='application/json')
    else:
        call = Call(session_uuid, call_uuid, source, destination, host)
        calls[call_uuid] = call
        logging.debug(f'call-uuid[{call_uuid}] added into calls dict')

    del_call, res = ivr_init(call)
    if del_call:
        logging.debug(f'Deleting call-uuid[{call_uuid}] from calls dict')
        del calls[call_uuid]
        call_ended.append(call_uuid)
    return jsonify(res)


@app.route('/voice/call-status', methods=['POST'])
def call_status():
    """
      Route received for webhook about call
    """

    if 'mocean-call-uuid' in request.form:
        call_uuid = request.form.get('mocean-call-uuid')
        logging.info(f'### Call status received [{call_uuid}] ###')
        for k, v in request.form.items():
            logging.info(f'\t{k}:{v}')

        if request.form.get('mocean-call-uuid') in calls \
                and request.form.get('mocean-status') == 'HANGUP':
            logging.debug(f'Deleting call-uuid[{call_uuid}] from calls dict')
            del calls[call_uuid]
            call_ended.append(call_uuid)
        return Response('', status=204, mimetype='text/plain')
    else:
        return invalid_response()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='5000')
