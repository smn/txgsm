from twisted.test import proto_helpers

from txgsm.tests.base import TxGSMBaseTestCase
from txgsm.utils import USSDConsole

from mock import Mock


class USSDConsoleTestCase(TxGSMBaseTestCase):

    def setUp(self):
        super(USSDConsoleTestCase, self).setUp()
        self.exit = Mock()
        self.console = USSDConsole(self.modem, on_exit=self.exit)
        self.console_transport = proto_helpers.StringTransport()
        self.console.makeConnection(self.console_transport)

    def test_dial_single_screen_session(self):
        d = self.console.dial('*100#')
        self.assertExchange(
            input=['AT+CUSD=1,"*100#",15'],
            output=[
                'OK',
                '+CUSD: 2,"foo",25'
            ])
        self.assertEqual(self.console_transport.value(), 'foo\n')
        return d

    def test_dial_multiple_screen_session(self):
        d = self.console.dial('*100#')
        self.assertExchange(
            input=['AT+CUSD=1,"*100#",15'],
            output=[
                'OK',
                '+CUSD: 1,"what is your name?",25'
            ])
        self.assertEqual(self.console_transport.value(),
                         'what is your name?\n%s> ' % (self.console.prefix,))
        self.console_transport.clear()
        self.console.lineReceived('foo')
        self.assertExchange(
            input=['AT+CUSD=1,"foo",15'],
            output=[
                'OK',
                '+CUSD: 2,"thanks!",25'
            ])
        self.assertEqual(self.console_transport.value(), 'thanks!\n')
        self.assertTrue(self.exit.called)
        return d
