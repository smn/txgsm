# -*- test-case-name: txgsm.tests.test_protocol -*-
# -*- coding: utf-8 -*-
import re

from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver
from twisted.internet.defer import (
    Deferred, maybeDeferred, DeferredList, succeed)
from twisted.python import log

from functools import partial
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
        self.triggers = defaultdict(list)
        self.buffer = b''
        self.buffer_results = []

    def log(self, *args):
        if self.verbose:
            log.msg(*args)

    def connectionMade(self):
        log.msg('Connection made')

    def trigger(self, pattern):
        """
        Returns a deferred that's fired when a pattern is recognised
        as an unsullicited response from the modem.

        :param str pattern:
            The pattern to be on the lookout for (i.e. ``+CRING``)
        """
        d = Deferred()
        self.triggers[pattern].append(d)
        return d

    def send_command(self, command, pattern, timeout=None, expect_prompt=False):
        """
        Send a command to the modem. This function returns a deferred that's
        fired when the response from the modem matches ``pattern``.

        :param str command:
            The AT command to send to the GSM modem.

        :param SRE_pattern pattern:
            A compiled regular expression matching the response to be expecting
            back which signals the response expected for this command. This
            will result in the returned Deferred being fired with response as
            the payload.

        :param float timeout:
            How many seconds to wait for a response before cancellined the
            Deferred. This will result in the Deferred's ``errback`` being
            fired with a ``CancelledError``.

        :param bool expect_prompt:
            A flag whether or not to expect a prompt from the GSM modem.
            If ``True`` the Deferred will fire when the response returned
            from the modem matches the pattern immediately.
            By default this is ``False`` which means the Deferred returned
            is only fired after the modem has returned ``OK`` or ``ERROR``.
            NOTE: This only works in raw mode.
        """
        self.debug('Sending: %r, expecting pattern: %r, prompt: %r' % (
            command, (pattern.pattern if pattern else pattern), expect_prompt))
        d = Deferred()
        d.addCallback(self.debug)
        d.addCallback(self.parse_responses_received, command, pattern)
        if timeout:
            reactor.callLater(timeout, d.cancel)
        self.command_queue.append((d, command, pattern, expect_prompt))
        self.sendLine(command)
        return d

    def debug(self, arg, prefix='DEBUG'):
        print('%s: %r' % (prefix, arg))
        return arg

    def start_raw_mode(self):
        self.debug('starting raw mode')
        self.setRawMode()
        # NOTE: Firing a succeed callback with an empty array, this
        #       allows us to chain further callbacks that append
        #       results coming from the modem
        return succeed([])

    def stop_raw_mode(self, args=None):
        self.debug('stopping raw mode')
        self.setLineMode(extra=self.buffer)
        return args

    def lineReceived(self, line):
        self.response_received(line)

    def response_received(self, line):
        # If we're not expecting anything, throw it straight through as
        # an unsolicited response from the modem

        if line == 'OK':
            responses_received, self.responses_received = (
                self.responses_received, [])
            d, _, _, _ = self.command_queue.pop()
            d.callback(responses_received)
        elif line == 'ERROR':
            responses_received, self.responses_received = (
                self.responses_received, [])
            d, _, _, _ = self.command_queue.pop()
            d.errback(responses_received)
        elif not self.command_queue:
            self.handle_unsolicited_responses([line])
        else:
            self.responses_received.append(line)

    def parse_responses_received(self, responses_received, command, pattern):
        if pattern is None:
            return {
                'command': command,
                'solicited_responses': [],
                'unsolicited_responses': [],
            }

        matches, unsolicited_responses = [], []
        for line in responses_received:
            if pattern.match(line):
                matches.append(line)
            else:
                unsolicited_responses.append(line)

        # NOTE: this does return a deferred and I could chain the matches
        #       response to it to allow errors to be captured but I am
        #       choosing not to. Since unsolicited responses can also be
        #       returned without any command from the application, the
        #       registered handlers need to handle their own errors anyway
        #       and so I'm favouring that for consistency.
        self.handle_unsolicited_responses(unsolicited_responses)

        d = {
            'command': command,
            'solicited_responses': matches,
            'unsolicited_responses': unsolicited_responses,
        }
        return d

    def handle_unsolicited_responses(self, unsolicited_responses):
        cloned_responses = unsolicited_responses[:]
        matched_patterns = []
        for response in unsolicited_responses:
            for pattern in self.triggers:
                if re.match(pattern, response):
                    matched_patterns.append(pattern)
                    deferreds = self.triggers[pattern]
                    for deferred in deferreds:
                        deferred.callback(response)
                    cloned_responses.remove(response)

        for pattern in matched_patterns:
            self.triggers.pop(pattern)

        if cloned_responses:
            self.log('Unhandled unsolicited responses: %r.' % (
                cloned_responses))

    def parse_raw_data_received(self, pattern, raw_buffer):
        return_results = []
        if not (pattern or raw_buffer):
            return return_results

        for match in pattern.finditer(raw_buffer):
            return_results.extend(match.groups())
        return return_results

    def rawDataReceived(self, data):
        if not self.command_queue:
            self.log('Unsollicited response received in raw mode: %r, '
                     'added to to buffer' % (data,))
            self.buffer += data
        elif data == ('OK' + self.delimiter):
            d, _, pattern, _ = self.command_queue.pop()
            d.callback(self.parse_raw_data_received(pattern, self.buffer))
            self.buffer = b''
        elif data == ('ERROR' + self.delimiter):
            d, _, pattern, _ = self.command_queue.pop()
            d.errback(self.parse_raw_data_received(pattern, self.buffer))
            self.buffer = b''
        else:
            self.buffer += data
            # NOTE: Peeking here to see if we're expecting a prompt reply.
            d, _, pattern, expect_prompt = self.command_queue[0]
            if expect_prompt and pattern.match(data):
                d, _, _, _ = self.command_queue.pop()
                d.callback(self.parse_raw_data_received(pattern, self.buffer))
                self.buffer = b''


class TxGSMProtocol(ATProtocol):

    def next(self, command, pattern=None, expect_prompt=False):
        def handler(result):
            d = self.send_command(command, pattern,
                                  expect_prompt=expect_prompt)
            d.addCallback(lambda r: (result + [r]))
            d.addErrback(log.err)
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
        d = self.start_raw_mode()
        for pdu in sms.to_pdu():
            d.addCallback(self.next(
                'AT+CMGS=%d' % (pdu.length,),
                pattern=re.compile(r'^(> )$'),
                expect_prompt=True))
            d.addCallback(self.next('%s%s' % (pdu.pdu, self.CTRL_Z)))

        d.addCallback(self.stop_raw_mode)

        return d

    def dial_ussd_code(self, code):
        d1 = self.trigger(r'\+CUSD')

        d2 = self.send_command('AT+CUSD=1,"%s",15' % (quote(code),),
                               pattern=None)
        d2.addCallback(lambda *a: d1)
        return d2

    def list_received_messages(self, status=4):
        d = self.start_raw_mode()
        d.addCallback(self.next(
            'AT+CMGL=%i' % (status,),
            pattern=re.compile(
                r'^(\+CMGL\: .+\r\n[A-Z0-9]+\r\n)', re.MULTILINE)))

        def parse_cmgl_response(responses):
            messages = []
            pattern = re.compile(
                r'^\+CMGL\: '
                r'(?P<index>\d*),'
                r'(?P<stat>\d*),'
                r'(?P<alpha>[\w]+)?,?'
                r'(?P<length>\d*)'
                r'\r\n(?P<pdu>[A-Z0-9]+)')

            for response in responses:
                for line in response['solicited_responses']:
                    match = pattern.match(line)
                    data = match.groupdict()
                    messages.append(SmsDeliver(data['pdu']))

            return messages

        d.addCallback(parse_cmgl_response)
        d.addCallback(self.stop_raw_mode)
        return d

    def probe(self):
        """
        See if we're talking to something GSM-like and if so,
        try and get some useful information out of it.
        """
        d = Deferred()
        d.addCallback(self.next('ATE0'))
        d.addCallback(self.next('AT+CIMI', pattern=re.compile(r'^(\d+)$')))
        d.addCallback(self.next('AT+CGMM', pattern=re.compile(r'^([\w\s]+)$')))
        reactor.callLater(0, d.callback, [])
        return d
