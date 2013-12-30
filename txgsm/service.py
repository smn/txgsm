# -*- test-case-name: txgsm.tests.test_service -*-
import sys
from pprint import pprint
from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import Service
from twisted.application.service import IServiceMaker
from twisted.internet.defer import inlineCallbacks, Deferred, returnValue
from twisted.internet import reactor, stdio
from twisted.internet.serialport import SerialPort
from twisted.python import log

from txgsm.protocol import TxGSMProtocol
from txgsm.utils import USSDConsole


class SendSMS(usage.Options):

    optParameters = [
        ["to-addr", None, None, "The address to send an SMS to."],
        ["message", None, None, "The message to send"],
    ]


class ListSMS(usage.Options):
    optParameters = [
        ['status', 's', 4, 'What messages to read (0: unread, 1: read, '
            '2: unsent, 3: sent, 4: all)'],
    ]


class USSDSession(usage.Options):

    optParameters = [
        ['code', None, None, "The USSD code to dial"],
    ]


class ProbeModem(usage.Options):
    pass


class Options(usage.Options):

    subCommands = [
        ['send-sms', None, SendSMS, "Send an SMS"],
        ['list-sms', None, ListSMS, "List SMSs on Modem"],
        ['ussd-session', None, USSDSession, 'Start a USSD session'],
        ['probe-modem', None, ProbeModem,
            'Probe the device to see if it is something modem-ish'],
    ]

    optFlags = [
        ["verbose", "v", "Log AT commands"],
    ]

    optParameters = [
        ["device", "d", None, "The device to connect to."],
    ]


class TxGSMService(Service):

    protocol = TxGSMProtocol
    serial_port_class = SerialPort

    def __init__(self, device, **conn_options):
        self.device = device
        self.conn_options = conn_options
        self.onProtocol = Deferred()
        self.onProtocol.addErrback(log.err)

    def getProtocol(self):
        return self.protocol()

    def startService(self):
        p = self.getProtocol()
        self.port = self.serial_port_class(p, self.device, reactor,
                                           **self.conn_options)
        self.onProtocol.callback(p)

    def stopService(self):
        self.port.loseConnection()


class TxGSMServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "txgsm"
    description = ("Utilities for talking to a GSM modem over USB via AT "
                   "commands.")
    options = Options

    def makeService(self, options):
        device = options['device']
        service = TxGSMService(device)
        service.onProtocol.addCallback(self.set_verbosity, options)

        dispatch = {
            'send-sms': self.send_sms,
            'list-sms': self.list_sms,
            'ussd-session': self.ussd_session,
            'probe-modem': self.probe_modem,
        }

        callback = dispatch.get(options.subCommand)
        if callback:
            service.onProtocol.addCallback(callback, options)
            return service
        else:
            sys.exit(str(options))

    def set_verbosity(self, modem, options):
        modem.verbose = options['verbose']
        return modem

    @inlineCallbacks
    def send_sms(self, modem, options):
        cmd_options = options.subOptions
        yield modem.configure_modem()
        result = yield modem.send_sms(cmd_options['to-addr'],
                                      cmd_options['message'])
        returnValue(self.shutdown(result))

    @inlineCallbacks
    def list_sms(self, modem, options):
        cmd_options = options.subOptions
        yield modem.configure_modem()
        messages = yield modem.list_received_messages(
            int(cmd_options['status']))
        for message in messages:
            log.msg(message.data)
        returnValue(self.shutdown())

    @inlineCallbacks
    def ussd_session(self, modem, options):
        log.msg('Connecting to modem.')
        cmd_options = options.subOptions
        yield modem.configure_modem()
        log.msg('Connected, starting console for: %s' % (cmd_options['code'],))
        console = USSDConsole(modem, on_exit=self.shutdown)
        sio = stdio.StandardIO(console)
        log.msg('Dialing: %s' % (cmd_options['code'],))
        yield console.dial(cmd_options['code'])
        returnValue(sio)

    @inlineCallbacks
    def probe_modem(self, modem, options):
        result = yield modem.probe()
        [_, imsi_result, manufacturer_result] = result
        imsi, ok = imsi_result['response']
        manufacturer, ok = manufacturer_result['response']
        log.msg('Manufacturer: %s' % (manufacturer,))
        log.msg('IMSI: %s' % (imsi,))
        self.shutdown()

    def shutdown(self, resp=None):
        reactor.callLater(0, reactor.stop)
