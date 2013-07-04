# -*- test-case-name: txgsm.tests.test_txgsm -*-
# -*- coding: utf-8 -*-
from twisted.internet.serialport import SerialPort
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver
from twisted.internet.defer import Deferred
from twisted.application.service import Service
from twisted.python import log

from .utils import quote

from messaging.sms import SmsSubmit


class TxGSMProtocol(LineReceiver):

    CTRL_Z = '\x1a'
    delimiter = '\r\n'
    verbose = False

    def __init__(self):
        # AT switches being purely line oriented and sometimes not
        # especially when sending multipart SMSs which has a '^> $' prompt
        # without a '\r\n' that we need to wait for.
        # As a result using lineReceived() does not always work.
        self.setRawMode()
        self.deferreds = []
        self.buffer = b''

    def log(self, msg):
        if self.verbose:
            log.msg(msg)

    def connectionMade(self):
        self.log('Connection made')

    def send_command(self, command, expect='OK', timeout=None):
        self.log('Sending: %r' % (command,))
        resp = Deferred()
        resp.addCallback(self.debug)
        if timeout:
            reactor.callLater(timeout, resp.cancel)
        self.deferreds.append((command, expect, resp))
        self.sendLine(command)
        return resp

    def debug(self, resp):
        self.log('Received: %r' % (resp,))
        return resp

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
        for pdu in sms.to_pdu():
            d.addCallback(self.next(
                'AT+CMGS=%d' % (pdu.length,),
                expect='> '))
            d.addCallback(self.next('%s%s' % (pdu.pdu, self.CTRL_Z)))

        d.callback([])
        return d

    def dial_ussd_code(self, code):
        return self.send_command('AT+CUSD=1,"%s",15' % (quote(code),),
                                 expect='+CUSD')

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


class TxGSMService(Service):

    protocol = TxGSMProtocol
    serial_port_class = SerialPort

    def __init__(self, device, **conn_options):
        self.device = device
        self.conn_options = conn_options
        self.onProtocol = Deferred()
        self.onProtocol.addErrback(log.err)

    def startService(self):
        p = self.protocol()
        self.port = self.serial_port_class(p, self.device, reactor,
                                           **self.conn_options)
        self.onProtocol.callback(p)

    def stopService(self):
        self.port.loseConnection()
