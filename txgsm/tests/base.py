from twisted.trial.unittest import TestCase
from twisted.internet.defer import inlineCallbacks, Deferred
from twisted.internet import reactor
from twisted.test import proto_helpers
from twisted.python import log

from txgsm.txgsm import TxGSMProtocol


class TxGSMBaseTestCase(TestCase):

    def setUp(self):
        self.modem = TxGSMProtocol()
        self.modem.verbose = True
        self.modem_transport = proto_helpers.StringTransport()
        self.modem.makeConnection(self.modem_transport)

    def reply(self, data, delimiter=None, modem=None):
        modem = modem or self.modem
        dl = delimiter or modem.delimiter
        modem.dataReceived(data + dl)

    def wait_for_next_commands(self, clear=True, modem=None, transport=None):

        modem = modem or self.modem
        transport = transport or self.modem_transport

        d = Deferred()

        def check_for_input():
            if not transport.value():
                reactor.callLater(0, check_for_input)
                return

            commands = transport.value().split(modem.delimiter)

            if clear:
                transport.clear()

            d.callback(filter(None, commands))

        check_for_input()
        return d

    @inlineCallbacks
    def assertCommands(self, commands, clear=True, modem=None, transport=None):
        received_commands = yield self.wait_for_next_commands(
            clear=clear, modem=modem, transport=transport)
        self.assertEqual(commands, received_commands)

    @inlineCallbacks
    def assertExchange(self, input, output, clear=True, modem=None,
                       transport=None):
        yield self.assertCommands(input, clear=clear, modem=modem,
                                  transport=transport)
        for reply in output:
            self.reply(reply, modem=modem)


# Shamelessly copyied from @Hodgestar's contribution to
# https://github.com/praekelt/vumi/
class LogCatcher(object):

    def __init__(self):
        self.logs = []

    def __enter__(self):
        log.theLogPublisher.addObserver(self.logs.append)
        return self

    def __exit__(self, *exc_info):
        log.theLogPublisher.removeObserver(self.logs.append)
