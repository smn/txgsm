from twisted.trial.unittest import TestCase
from twisted.internet.defer import inlineCallbacks, Deferred
from twisted.test import proto_helpers
from twisted.python import log

from txgsm.txgsm import TxGSMProtocol


class TxGSMBaseTestCase(TestCase):

    def setUp(self):
        self.modem = TxGSMProtocol()
        self.modem.verbose = True
        self.modem_transport = proto_helpers.StringTransport()
        self.modem.makeConnection(self.modem_transport)

    def reply(self, data, delimiter=None):
        dl = delimiter or self.modem.delimiter
        self.modem.dataReceived(data + dl)

    def wait_for_next_commands(self, clear=True):

        d = Deferred()

        def check_for_input():
            if not self.modem_transport.value():
                reactor.callLater(0, check_for_input)
                return

            commands = self.modem_transport.value().split(
                self.modem.delimiter)

            if clear:
                self.modem_transport.clear()

            d.callback(filter(None, commands))

        check_for_input()
        return d

    @inlineCallbacks
    def assertCommands(self, commands):
        received_commands = yield self.wait_for_next_commands()
        self.assertEqual(commands, received_commands)

    @inlineCallbacks
    def assertExchange(self, input, output):
        yield self.assertCommands(input)
        for reply in output:
            self.reply(reply)


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
