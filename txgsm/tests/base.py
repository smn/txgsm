from twisted.trial.unittest import TestCase
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

    def get_next_commands(self, clear=True):
        commands = self.modem_transport.value().split(self.modem.delimiter)
        if clear:
            self.modem_transport.clear()
        return filter(None, commands)

    def assertCommands(self, commands):
        self.assertEqual(commands, self.get_next_commands())

    def assertExchange(self, input, output):
        self.assertCommands(input)
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
