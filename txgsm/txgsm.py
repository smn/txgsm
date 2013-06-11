# -*- test-case-name: txgsm.tests.test_txgsm -*-
from twisted.internet.serialport import SerialPort
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from twisted.internet.defer import Deferred, inlineCallbacks
from twisted.application.service import Service
from twisted.python import log

from messaging.sms import SmsSubmit


class TxGSMProtocol(LineReceiver):

    CTRL_Z = '\x1a'

    def __init__(self):
        self.deferreds = []
        self.buffer = []

    @inlineCallbacks
    def connectionMade(self):
        log.msg('Connection made')
        r = yield self.configureProtocol()
        print 'r', r
        r = yield self.sendSMS('+27764493806', 'hello world')
        print 'r'

    def sendCommand(self, command, expect='OK'):
        log.msg('Sending: %s' % (command,))
        resp = Deferred()
        self.deferreds.append((expect, resp))
        self.sendLine(command)
        return resp

    def debug(self, resp):
        log.msg('resp: %s' % (resp,))
        return resp

    def configureProtocol(self):
        d = self.sendCommand('AT+CMGF=0')  # PDU mode
        d.addCallback(self.debug)
        return d

    @inlineCallbacks
    def sendSMS(self, msisdn, text):
        sms = SmsSubmit(msisdn, text)
        for pdu in sms.to_pdu():
            yield self.sendCommand('AT+CMGS=%d\r' % (pdu.length,),
                                   expect='> ')
            yield self.sendCommand('%s%s' % (pdu.pdu, self.CTRL_Z))

    def lineReceived(self, line):
        log.msg('Received line: %r' % (line,))
        self.buffer.append(line)
        print self.buffer
        expect, deferred = self.deferreds[0]
        if line == expect:
            print 'got expected!', expect
            expect, deferred = self.deferreds.pop(0)
            return_buffer, self.buffer = self.buffer, []
            deferred.callback(return_buffer)

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
