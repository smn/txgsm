# -*- test-case-name: txgsm.tests.test_protocol -*-
# -*- coding: utf-8 -*-
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver
from twisted.internet.defer import Deferred
from twisted.python import log

from collections import defaultdict

from .utils import quote

from messaging.sms import SmsSubmit, SmsDeliver


class ATProtocol(LineReceiver):
    CTRL_Z = '\x1a'
    delimiter = '\r\n'
    verbose = True

    def __init__(self):
        self.command_queue = []
        self.responses_received = []
        self.unsolicited_result_callbacks = defaultdict(list)
        self.solicited_result_queue = defaultdict(list)
        self.buffer = b''

    def log(self, *args):
        if self.verbose:
            log.msg(*args)

    def connectionMade(self):
        log.msg('Connection made')

    def register_unsolicited_result_callback(self, response, cb):
        """
        Register a callback function that should be called when ``response``
        is received from the modem when it was not necessarily expected.

        :param str response:
            The response to be on the lookout for (i.e. ``+CRING``)
        :param function cb:
            The callback function to call when ``response`` is seen.
        """
        self.unsolicited_result_callbacks[response].append(cb)

    def deregister_unsolicited_result_callback(self, response, cb):
        """
        Deregister a callback function for a specific response.

        :param str response:
            The response the callback was originally registered for.
        :param function cb:
            The callback function to remove.
        """
        self.unsolicited_result_callbacks[response].remove(cb)

    def send_command(self, command, expect='OK', timeout=None):
        """
        Send a command to the modem. This function returns a deferred that's
        fired when the value of ``expect`` is received from the modem.

        :param str expect:
            The AT response to be expecting back which signals the response
            expected for this command. This will result in the returned
            Deferred being fired with response as the payload.
        :param float timeout:
            How many seconds to wait for a response before cancellined the
            Deferred. This will result in the Deferred's ``errback`` being
            fired with a ``CancelledError``.
        """
        self.log('Sending: %r' % (command,))
        d = Deferred()
        d.addCallback(self.debug)
        if timeout:
            reactor.callLater(timeout, d.cancel)
        self.solicit_result(command, expect, d)
        self.sendLine(command)
        return d

    def debug(self, arg):
        log.msg('DEBUG: %r' % arg)
        return arg

    def solicit_result(self, command, expect, deferred):
        self.solicited_result_queue[expect].append((command, deferred))

    def lineReceived(self, line):
        if line == 'OK':
            responses_received, self.responses_received = (
                self.responses_received, [])
            d = self.command_queue.pop()
            d.callback(responses_received)
        elif line == 'ERROR':
            responses_received, self.responses_received = (
                self.responses_received, [])
            d = self.command_queue.pop()
            d.errback(responses_received)
        else:
            self.responses_received.append(line)

    def parse_responses_received(self, responses_received):
        for line in responses_received:
            result, _ = line.split(':', 1)
            expected_handlers = self.solicited_result_queue[result]
            if expected_handlers:
                # FIXME: possibility of a race condition here.
                command, deferred = expected_handlers.pop()
                deferred.callback({
                    'command': [command],
                    'expect': result,
                    'response': [line],
                })
                return

            unexpected_handlers = self.unsolicited_result_callbacks[result]
            for handler in unexpected_handlers:
                handler(line)


class TxGSMProtocol(ATProtocol):

    def next(self, command, expect='OK'):
        def handler(result):
            d = self.send_command(command, expect)
            d.addCallback(lambda r: result + [r])
            return d
        return handler

    def configure_modem(self):
        # Sensible defaults shamelessly copied from pygsm.
        d = Deferred()
        d.addCallback(self.next('ATE0'))  # Disable echo
        d.addCallback(self.next('AT+CMGF=0'))  # PDU mode
        d.addCallback(self.next('AT+CMEE=1'))  # More useful errors
        d.addCallback(self.next('AT+CSMS=1'))  # set SMS mode to phase 2+
        d.callback([])
        return d

    def send_sms(self, msisdn, text):
        sms = SmsSubmit(msisdn, text)
        # NOTE: The use of the Deferred here is a bit wonky
        #       I'm using it like this because it makes adding callbacks
        #       in a for-loop easier since we're potentially sending
        #       SMSs bigger than 160 chars.
        d = Deferred()
        d.addCallback(self.toggle_raw_mode)
        for pdu in sms.to_pdu():
            d.addCallback(self.next(
                'AT+CMGS=%d' % (pdu.length,),
                expect='> '))
            d.addCallback(self.next('%s%s' % (pdu.pdu, self.CTRL_Z)))

        d.addCallback(self.toggle_line_mode)
        d.callback([])

        return d

    def toggle_raw_mode(self, args):
        self.setRawMode()
        return args

    def toggle_line_mode(self, args):
        self.setLineMode(extra=self.buffer)
        return args

    def dial_ussd_code(self, code):
        return self.send_command('AT+CUSD=1,"%s",15' % (quote(code),),
                                 expect='+CUSD')

    def list_received_messages(self, status=4):
        d = self.send_command('AT+CMGL=%i' % (status,))

        def parse_cmgl_response(result):
            response = result['response']
            # Lines alternative between the +CMGL response and the
            # actual PDU containing the SMS
            found = False
            messages = []
            for line in response:
                if line.startswith('+CMGL:'):
                    found = True
                elif found:
                    messages.append(SmsDeliver(line))
                    found = False

            return messages

        d.addCallback(parse_cmgl_response)
        return d

    def probe(self):
        """
        See if we're talking to something GSM-like and if so,
        try and get some useful information out of it.
        """
        d = Deferred()
        d.addCallback(self.next('ATE0'))
        d.addCallback(self.next('AT+CIMI'))
        d.addCallback(self.next('AT+CGMM'))
        reactor.callLater(0, d.callback, [])
        return d

    def rawDataReceived(self, data):
        self.buffer += data

        if not self.deferreds:
            log.err('Unsollicited response: %r' % (data,))
            return

        _, expect, _ = self.deferreds[0]

        if expect in self.buffer:
            command, expect, deferred = self.deferreds.pop(0)
            return_buffer, self.buffer = self.buffer, b''
            result = {
                'command': [command],
                'expect': expect,
                'response': filter(None, return_buffer.split(self.delimiter))
            }
            deferred.callback(result)
