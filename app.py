import logging
import json

from flask import Flask, Response, request, jsonify
from utils.mccc_gen import ivr_init, ivr_check
from utils.call_info import Call

app = Flask(__name__)

calls = {}

def invalid_response():
    return Response('{"status": "Invalid request"}', status=400, mimetype='application/json')

@app.route('/voice/collect-mccc', methods=['POST'])
def collect_mccc():
    session_uuid = request.form.get('mocean-session-uuid')
    call_uuid = request.form.get('mocean-call-uuid')
    digits = request.form.get('mocean-digits')
    logging.info(f'### Collect MCCC received from [{call_uuid}] ###')
    host = request.headers['Host']

    if call_uuid not in calls:
        call = Call(session_uuid, call_uuid, None, None, host)
        calls[call_uuid] = call
        logging.debug(f'call-uuid[{call_uuid}] added into calls dict')
        # return Response(ret, status=200, mimetype='application/json')
        return jsonify(ivr_init(call))
    else:
        call = calls[call_uuid]
        # return Response(ret, status=200, mimetype='application/json')
        res = jsonify(ivr_check(digits, call))
        return res


@app.route('/voice/inbound-mccc', methods=['POST'])
def inbound_mccc():
    session_uuid = request.form.get('mocean-session-uuid')
    call_uuid = request.form.get('mocean-call-uuid')
    destination = request.form.get('mocean-to')
    source = request.form.get('mocean-from')

    logging.info(f'### Call received from [{source}], assigned call-uuid[{call_uuid}] ###')
    host = request.headers['Host']

    if call_uuid in calls:
        logging.warning(f'call-uuid[{call_uuid}] is in calls, should not use `voice/inbound-mccc\' path')
        call = calls[call_uuid]
    else:
        call = Call(session_uuid, call_uuid, source, destination, host)
        calls[call_uuid] = call
        logging.debug(f'call-uuid[{call_uuid}] added into calls dict')

    ret = ivr_init(call)
    return jsonify(ret)

@app.route('/voice/call-status', methods=['POST'])
def call_status():
    session_uuid = request.form.get('mocean-session-uuid')
    call_uuid = request.form.get('mocean-call-uuid')
    destination = request.form.get('mocean-to')
    source = request.form.get('mocean-from')
    direction = request.form.get('mocean-direction')

    logging.info(f'### Call status received [{call_uuid}] ###')
    logging.info(f'\tcall-uuid:{call_uuid}')
    logging.info(f'\tsession-uuid:{session_uuid}')
    logging.info(f'\tsource number:{source}')
    logging.info(f'\tdestination number:{destination}')
    logging.info(f'\tcall direction{direction}\n')

    return Response('', status=204, mimetype='text/plain')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True)
