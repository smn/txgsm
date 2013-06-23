import sys
from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor, stdio
from twisted.python import log

from txgsm.txgsm import TxGSMService
from txgsm.utils import USSDConsole


class SendSMS(usage.Options):

    optParameters = [
        ["to-addr", None, None, "The address to send an SMS to."],
        ["message", None, None, "The message to send"],
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


class TxGSMMaker(object):
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
        yield modem.send_sms(cmd_options['to-addr'], cmd_options['message'])
        reactor.stop()

    @inlineCallbacks
    def ussd_session(self, modem, options):
        log.msg('Connecting to modem.')
        cmd_options = options.subOptions
        yield modem.configure_modem()
        log.msg('Connected, starting console for: %s' % (cmd_options['code'],))
        console = USSDConsole(modem, on_exit=self.shutdown)
        stdio.StandardIO(console)
        log.msg('Dialing: %s' % (cmd_options['code'],))
        yield console.dial(cmd_options['code'])

    @inlineCallbacks
    def probe_modem(self, modem, options):
        result = yield modem.probe()
        [_, imsi, _, manufacturer, _] = result
        log.msg('Manufacturer: %s' % (manufacturer,))
        log.msg('IMSI: %s' % (imsi,))
        reactor.stop()

    def shutdown(self, resp):
        reactor.callLater(2, reactor.stop)


serviceMaker = TxGSMMaker()
