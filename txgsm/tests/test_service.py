from twisted.internet.defer import inlineCallbacks

from txgsm.tests.base import TxGSMBaseTestCase
from txgsm.service import TxGSMServiceMaker, TxGSMService, Options

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

    def patch_shutdown(self, result):
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
