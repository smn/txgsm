from twisted.internet.defer import inlineCallbacks

from txgsm.tests.base import TxGSMBaseTestCase, LogCatcher


class TxGSMTestCase(TxGSMBaseTestCase):

    timeout = 1

    @inlineCallbacks
    def test_configure_modem(self):
        d = self.modem.configureModem()
        self.assertExchange(['AT+CMGF=0'], ['OK'])
        self.assertExchange(['ATE0'], ['OK'])
        self.assertExchange(['AT+CMEE=1'], ['OK'])
        self.assertExchange(['AT+WIND=0'], ['OK'])
        self.assertExchange(['AT+CSMS=1'], ['OK'])
        self.assertExchange(['AT+CSQ'], ['OK'])
        response = yield d
        self.assertEqual(response, ['OK'])

    @inlineCallbacks
    def test_send_sms(self):
        d = self.modem.sendSMS('+27761234567', 'hello world')
        self.assertCommands(['AT+CMGS=23'])
        self.reply('> ', delimiter='')
        [pdu_payload] = self.get_next_commands()
        self.reply('OK')
        response = yield d
        self.assertEqual(response, ['OK'])

    @inlineCallbacks
    def test_send_multipart_sms(self):
        d = self.modem.sendSMS('+27761234567', '1' * 180)
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
        d = self.modem.dialUSSDCode('*100#')
        self.assertExchange(
            input=['AT+CUSD=1,"*100#",15'],
            output=[
                'OK',
                ('+CUSD: 2,"Your balance is R48.70. Out of Airtime? '
                 'Dial *111# for Airtime Advance. T&Cs apply.",255')
            ])
        response = yield d
        self.assertEqual(response[0], 'OK')
        self.assertTrue(response[1].startswith('+CUSD: 2'))

    def test_dealing_with_unexpected_events(self):
        with LogCatcher() as catcher:
            self.reply('+FOO')
            [err_log] = catcher.logs
            self.assertTrue('Unsollicited response' in err_log['message'][0])
            self.assertTrue('+FOO' in err_log['message'][0])
