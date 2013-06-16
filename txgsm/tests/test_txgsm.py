from twisted.trial.unittest import TestCase
from twisted.internet.defer import inlineCallbacks
from twisted.test import proto_helpers

from txgsm.txgsm import TxGSMProtocol


class TxGSMTextCase(TestCase):

    def setUp(self):
        self.protocol = TxGSMProtocol()
        self.protocol.verbose = True
        self.transport = proto_helpers.StringTransport()
        self.protocol.makeConnection(self.transport)
        self._command_index = 0

    def reply(self, data):
        self.protocol.dataReceived(data)

    def get_next_commands(self):
        commands = self.transport.value().split(self.protocol.delimiter)
        self.transport.clear()
        return filter(None, commands)

    def assertCommands(self, commands):
        self.assertEqual(commands, self.get_next_commands())

    @inlineCallbacks
    def test_send_sms(self):
        d = self.protocol.sendSMS('+27761234567', 'hello world')
        self.assertCommands(['AT+CMGS=23'])
        self.reply('> ')
        [pdu_payload] = self.get_next_commands()
        self.reply('OK')
        response = yield d
        self.assertEqual(response, ['OK'])
