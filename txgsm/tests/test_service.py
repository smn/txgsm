from twisted.internet.defer import inlineCallbacks

from txgsm.tests.base import TxGSMBaseTestCase, LogCatcher
from txgsm.service import TxGSMServiceMaker, TxGSMService, Options
from txgsm.utils import USSDConsole

from mock import Mock


class TxGSMServiceTestCase(TxGSMBaseTestCase):

    def setUp(self):
        super(TxGSMServiceTestCase, self).setUp()
        TxGSMService.serial_port_class = Mock()
        self.patch(TxGSMService, 'getProtocol', self.patch_get_protocol)
        self.patch(TxGSMServiceMaker, 'shutdown', self.patch_shutdown)

    def patch_get_protocol(self):
        #  Protocol created by TxGSMBaseTestCase
        return self.modem

    def patch_shutdown(self, result=None):
        # noop, pass along result instead of shutting down
        return result

    @inlineCallbacks
    def assert_configure_modem(self):
        yield self.assertExchange(['ATE0'], ['OK'])
        yield self.assertExchange(['AT+CMGF=0'], ['OK'])
        yield self.assertExchange(['AT+CMEE=1'], ['OK'])
        yield self.assertExchange(['AT+CSMS=1'], ['OK'])

    def make_service(self, command, options):
        args = ['--device', '/dev/foo', command]
        args.extend(options)
        service_options = Options()
        service_options.parseOptions(args)
        service_maker = TxGSMServiceMaker()
        service = service_maker.makeService(service_options)
        service.startService()
        return service

    @inlineCallbacks
    def test_send_sms_command(self):
        service = self.make_service('send-sms', [
            '--to-addr', '+27761234567',
            '--message', 'hello world',
        ])
        yield self.assert_configure_modem()
        yield self.assertCommands(['AT+CMGS=23'])
        self.reply('> ', delimiter='')
        [pdu_payload] = yield self.wait_for_next_commands()
        self.reply('OK')
        response = yield service.onProtocol
        self.assertEqual(response, [
            {
                'command': ['AT+CMGS=23'],
                'expect': '> ',
                'response': ['> ']
            },
            {
                'command': ['0001000B917267214365F700000B'
                            'E8329BFD06DDDF723619\x1a'],
                'expect': 'OK',
                'response': ['OK']
            }
        ])

    @inlineCallbacks
    def test_list_sms(self):
        service = self.make_service('list-sms', [
            '--status', 4
        ])
        yield self.assert_configure_modem()
        with LogCatcher() as catcher:
            yield self.assertExchange(
                input=['AT+CMGL=4'],
                output=[
                    '+CMGL: 1,0,,39',
                    ('07911326040011F5240B911326880736F40000111081017362' +
                     '401654747A0E4ACF41F4329E0E6A97E7F3F0B90C8A01'),
                    '+CMGL: 2,0,,39',
                    ('07911326040011F5240B911326880736F40000111081017323' +
                     '401654747A0E4ACF41F4329E0E6A97E7F3F0B90C9201'),
                    'OK'
                ])
            yield service.onProtocol
        [sms1_log, sms2_log] = catcher.logs
        self.assertEqual('This is text message 1',
                         sms1_log['message'][0]['text'])
        self.assertEqual('This is text message 2',
                         sms2_log['message'][0]['text'])

    @inlineCallbacks
    def test_ussd_session(self):
        responses = []
        self.patch(USSDConsole, 'handle_response', responses.append)

        service = self.make_service('ussd-session', [
            '--code', '*100#'
        ])
        yield self.assert_configure_modem()
        yield self.assertExchange(
            input=['AT+CUSD=1,"*100#",15'],
            output=[
                'OK',
                ('+CUSD: 2,"Your balance is R48.70. Out of Airtime? '
                 'Dial *111# for Airtime Advance. T&Cs apply.",255')
            ])
        standard_io = yield service.onProtocol
        standard_io.loseConnection()
        [ussd_resp] = responses
        self.assertEqual(ussd_resp['response'], [
            'OK',
            ('+CUSD: 2,"Your balance is R48.70. Out of Airtime? '
             'Dial *111# for Airtime Advance. T&Cs apply.",255')
        ])

    @inlineCallbacks
    def test_probe_modem(self):
        service = self.make_service('probe-modem', [])
        with LogCatcher() as catcher:
            yield self.assertExchange(['ATE0'], ['OK'])
            yield self.assertExchange(['AT+CIMI'], ['01234123412341234', 'OK'])
            yield self.assertExchange(['AT+CGMM'], ['Foo Bar Corp', 'OK'])
            yield service.onProtocol

        [entry1, entry2] = catcher.logs
        self.assertEqual(entry1['message'][0], 'Manufacturer: Foo Bar Corp')
        self.assertEqual(entry2['message'][0], 'IMSI: 01234123412341234')
