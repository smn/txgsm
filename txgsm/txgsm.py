# -*- test-case-name: txgsm.tests.test_txgsm -*-
from twisted.internet.serialport import SerialPort
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver
from twisted.internet.defer import Deferred, inlineCallbacks
from twisted.application.service import Service
from twisted.python import log

from messaging.sms import SmsSubmit


class TxGSMProtocol(LineReceiver):

    CTRL_Z = '\x1a'
    delimiter = '\r\n'

    def __init__(self):
        # AT switches between '\r' and '\r\n' a bit so
        # using lineReceived() does not always work.
        self.setRawMode()
        self.deferreds = []
        self.buffer = b''

    @inlineCallbacks
    def connectionMade(self):
        log.msg('Connection made')
        r = yield self.configureProtocol()
        r = yield self.sendSMS('+27YOURPHONENUMBERHERE',
            ('1' * 160) + ('2' * 2))

    def sendCommand(self, command, expect='OK', delimiter=None):
        log.msg('Sending: %r' % (command,))
        resp = Deferred()
        resp.addCallback(self.debug)
        self.deferreds.append((expect, resp))
        dl = delimiter or self.delimiter
        self.transport.write(command + dl)
        return resp

    def debug(self, resp):
        log.msg('Received: %r' % (resp,))
        return resp

    def next(self, command, expect='OK', delimiter=None):
        def handler(result):
            return self.sendCommand(command, expect)
        return handler

    def configureProtocol(self):
        d = self.sendCommand('AT+CMGF=0')  # PDU mode
        d.addCallback(self.next('ATE0'))
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
                expect='> ',
                delimiter='\r'))
            d.addCallback(self.next('%s%s' % (pdu.pdu, self.CTRL_Z)))

        d.callback(None)
        return d

    def rawDataReceived(self, data):
        self.buffer += data
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

    def connectionLost(self, reason):
        log.msg('Connection lost: %r' % (reason,))


class TxGSMService(Service):

    protocol = TxGSMProtocol

    def __init__(self, device, **conn_options):
        self.device = device
        self.conn_options = conn_options

    def startService(self):
        self.port = SerialPort(self.protocol(), self.device, reactor,
                               **self.conn_options)
