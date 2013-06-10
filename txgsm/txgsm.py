# -*- test-case-name: txgsm.tests.test_txgsm -*-
from twisted.internet.serialport import SerialPort
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from twisted.application.service import Service
from twisted.python import log


class TxGSMProtocol(LineReceiver):

    def connectionMade(self):
        log.msg('Connection made')
        self.sendLine('AT+CGMI')
        self.sendLine('AT+CGMM')
        self.sendLine('AT+CGSN')
        self.sendLine('AT+CGMR')
        self.sendLine('AT+CNUM')
        self.sendLine('AT+CIMI')

    def lineReceived(self, line):
        log.msg('Received line: %r' % (line,))

    def connectionLost(self, reason):
        log.msg('Connection lost: %r' % (reason,))


class TxGSMService(Service):

    def __init__(self, device, **conn_options):
        self.device = device
        self.conn_options = conn_options

    def startService(self):
        self.port = SerialPort(TxGSMProtocol(), self.device, reactor,
                               **self.conn_options)
