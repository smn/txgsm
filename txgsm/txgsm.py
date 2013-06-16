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
        # AT switches between '\r' and '\r\n' a bit so
        # using lineReceived() does not always work.
        self.setRawMode()
        self.deferreds = []
        self.buffer = b''

    def log(self, msg):
        if self.verbose:
            log.msg(msg)

    def connectionMade(self):
        self.log('Connection made')

    def sendCommand(self, command, expect='OK'):
        self.log('Sending: %r' % (command,))
        resp = Deferred()
        resp.addCallback(self.debug)
        self.deferreds.append((expect, resp))
        self.sendLine(command)
        return resp

    def debug(self, resp):
        self.log('Received: %r' % (resp,))
        return resp

    def next(self, command, expect='OK'):
        def handler(result):
            return self.sendCommand(command, expect)
        return handler

    def configureModem(self):
        d = self.sendCommand('AT+CMGF=0')  # PDU mode
        d.addCallback(self.next('ATE0'))  # Disable echo
        d.addCallback(self.next('AT+CMEE=1'))  # More useful errors
        d.addCallback(self.next('AT+WIND=0'))  # Don't send unsollicited events
        d.addCallback(self.next('AT+CSMS=1'))  # set SMS mode to phase 2+
        d.addCallback(self.next('AT+CSQ'))
        return d

    def sendSMS(self, msisdn, text):
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

        d.callback(None)
        return d

    def dialUSSDCode(self, code):
        return self.sendCommand('AT+CUSD=1,"%s",15' % (quote(code),),
                                expect='+CUSD')

    def rawDataReceived(self, data):
        self.buffer += data

        if not self.deferreds:
            log.err('Unsollicited response: %r' % (data,))
            return

        expect, deferred = self.deferreds[0]

        if expect in self.buffer:
            expect, deferred = self.deferreds.pop(0)
            return_buffer, self.buffer = self.buffer, b''
            if return_buffer.endswith(self.delimiter):
                value = self.parseResponse(return_buffer)
            else:
                value = self.parseOutput(return_buffer)

            deferred.callback(value)

    def parseResponse(self, output):
        return filter(None, output.split(self.delimiter))

    def parseOutput(self, output):
        return filter(None, output.split(self.delimiter))


class TxGSMService(Service):

    protocol = TxGSMProtocol

    def __init__(self, device, **conn_options):
        self.device = device
        self.conn_options = conn_options
        self.onProtocol = Deferred()
        self.onProtocol.addErrback(log.err)

    def startService(self):
        p = self.protocol()
        self.port = SerialPort(p, self.device, reactor,
                               **self.conn_options)
        self.onProtocol.callback(p)

    def stopService(self):
        self.port.loseConnection()
