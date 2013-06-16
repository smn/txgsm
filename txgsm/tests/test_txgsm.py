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

    def reply(self, data, delimiter=None):
        self.protocol.dataReceived(data)

    def get_next_commands(self):
        commands = self.transport.value().split(self.protocol.delimiter)
        self.transport.clear()
        return filter(None, commands)

    def assertCommands(self, commands):
        self.assertEqual(commands, self.get_next_commands())

    def expectExchange(self, command, reply):
        self.assertCommands([command])
        self.reply(reply)

    @inlineCallbacks
    def test_configure_modem(self):
        d = self.protocol.configureModem()
        self.expectExchange('AT+CMGF=0', 'OK')
        self.expectExchange('ATE0', 'OK')
        self.expectExchange('AT+CMEE=1', 'OK')
        self.expectExchange('AT+WIND=0', 'OK')
        self.expectExchange('AT+CSMS=1', 'OK')
        self.expectExchange('AT+CSQ', 'OK')
        response = yield d
        self.assertEqual(response, ['OK'])

    @inlineCallbacks
    def test_send_sms(self):
        d = self.protocol.sendSMS('+27761234567', 'hello world')
        self.assertCommands(['AT+CMGS=23'])
        self.reply('> ', delimiter='')
        [pdu_payload] = self.get_next_commands()
        self.reply('OK')
        response = yield d
        self.assertEqual(response, ['OK'])
