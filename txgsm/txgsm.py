# -*- test-case-name: txgsm.tests.test_txgsm -*-
from twisted.internet.protocol import Protocol, Factory
from twisted.internet.serialport import SerialPort
from twisted.internet import reactor
from twisted.application.service import Service
from twisted.python import log


class TxGSMProtocol(Protocol):
    def connectionMade(self):
        log.msg('Connection made')
        self.transport.write('AT+CUSD=1,"*120*8864#"\r\n')

    def dataReceived(self, data):
        log.msg('Received data: %r' % (data,))

    def connectionLost(self, reason):
        log.msg('Connection lost: %r' % (reason,))


class TxGSMFactory(Factory):
    protocol = TxGSMProtocol


class TxGSMService(Service):

    def __init__(self, device, **conn_options):
        self.device = device
        self.conn_options = conn_options

    def startService(self):
        self.port = SerialPort(TxGSMProtocol(), self.device, reactor,
                               **self.conn_options)
