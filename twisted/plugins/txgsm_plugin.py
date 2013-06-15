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


class Options(usage.Options):

    subCommands = [
        ['send-sms', None, SendSMS, "Send an SMS"],
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
        if options.subCommand == 'send-sms':
            service.onProtocol.addCallback(self.send_sms,
                                           options.subOptions)
        return service

    @inlineCallbacks
    def send_sms(self, modem, options):
        yield modem.configureModem()
        yield modem.sendSMS(options['to-addr'], options['message'])
        reactor.stop()


serviceMaker = TxGSMMaker()
