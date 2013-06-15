import sys
from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor
from twisted.python import log

from txgsm.txgsm import TxGSMService


class SendSMS(usage.Options):

    optParameters = [
        ["to-addr", None, None, "The address to send an SMS to."],
        ["message", None, None, "The message to send"],
    ]


class USSDSession(usage.Options):

    optParameters = [
        ['code', None, None, "The USSD code to dial"],
    ]


class Options(usage.Options):

    subCommands = [
        ['send-sms', None, SendSMS, "Send an SMS"],
        ['ussd-session', None, USSDSession, 'Start a USSD session']
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
        log.msg('Using device: %r' % (device,))
        service = TxGSMService(device)

        dispatch = {
            'send-sms': self.send_sms,
            'ussd-session': self.ussd_session,
        }

        callback = dispatch.get(options.subCommand)
        if callback:
            service.onProtocol.addCallback(callback, options.subOptions)
            return service
        else:
            sys.exit(str(options))

    @inlineCallbacks
    def send_sms(self, modem, options):
        yield modem.configureModem()
        yield modem.sendSMS(options['to-addr'], options['message'])
        reactor.stop()

    @inlineCallbacks
    def ussd_session(self, modem, options):
        yield modem.configureModem()
        r = yield modem.sendCommand('AT+CUSD=1,"%s",15' % options['code'])
        print 'r', r



serviceMaker = TxGSMMaker()
