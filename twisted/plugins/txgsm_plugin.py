from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.python import log


class Options(usage.Options):
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
        return

serviceMaker = TxGSMMaker()
