from twisted.trial.unittest import TestCase
from twisted.internet.defer import inlineCallbacks
from twisted.test import proto_helpers

from txgsm.txgsm import TxGSMProtocol


class TxGSMTextCase(TestCase):

    timeout = 1

    def setUp(self):
        self.protocol = TxGSMProtocol()
        self.transport = proto_helpers.StringTransport()
        self.protocol.makeConnection(self.transport)

    def reply(self, data, delimiter=None):
        dl = delimiter or self.protocol.delimiter
        self.protocol.dataReceived(data + dl)

    def get_next_commands(self, clear=True):
        commands = self.transport.value().split(self.protocol.delimiter)
        if clear:
            self.transport.clear()
        return filter(None, commands)

    def assertCommands(self, commands):
        self.assertEqual(commands, self.get_next_commands())

    def expectExchange(self, input, output):
        self.assertCommands(input)
        for reply in output:
            self.reply(reply)

    @inlineCallbacks
    def test_configure_modem(self):
        d = self.protocol.configureModem()
        self.expectExchange(['AT+CMGF=0'], ['OK'])
        self.expectExchange(['ATE0'], ['OK'])
        self.expectExchange(['AT+CMEE=1'], ['OK'])
        self.expectExchange(['AT+WIND=0'], ['OK'])
        self.expectExchange(['AT+CSMS=1'], ['OK'])
        self.expectExchange(['AT+CSQ'], ['OK'])
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

    @inlineCallbacks
    def test_send_multipart_sms(self):
        d = self.protocol.sendSMS('+27761234567', '1' * 180)
        self.assertCommands(['AT+CMGS=153'])
        self.reply('> ', delimiter='')
        [pdu_payload] = self.get_next_commands()
        self.reply('OK')
        self.assertCommands(['AT+CMGS=43'])
        self.reply('> ', delimiter='')
        [pdu_payload] = self.get_next_commands()
        self.reply('OK')
        response = yield d
        self.assertEqual(response, ['OK'])

    @inlineCallbacks
    def test_ussd_session(self):
        d = self.protocol.dialUSSDCode('*100#')
        self.expectExchange(
            input=['AT+CUSD=1,"*100#",15'],
            output=[
                'OK',
                ('+CUSD: 2,"Your balance is R48.70. Out of Airtime? '
                 'Dial *111# for Airtime Advance. T&Cs apply.",255')
            ])
        response = yield d
        self.assertEqual(response[0], 'OK')
        self.assertTrue(response[1].startswith('+CUSD: 2'))

