from twisted.trial.unittest import TestCase
from twisted.internet.defer import inlineCallbacks
from twisted.test import proto_helpers

from txgsm.tests.base import TxGSMBaseTestCase
from txgsm.utils import USSDConsole


class USSDConsoleTestCase(TxGSMBaseTestCase):

    def setUp(self):
        super(USSDConsoleTestCase, self).setUp()
        self.console = USSDConsole(self.modem, on_exit=self.on_exit)
        self.console_transport = proto_helpers.StringTransport()
        self.console.makeConnection(self.console_transport)

    def on_exit(self, *args, **kwargs):
        return True

    def test_dial(self):
        d = self.console.dial('*100#')
        self.assertExchange(
            input=['AT+CUSD=1,"*100#",15'],
            output=[
                'OK',
                '+CUSD: 2,"foo",25'
            ])
        self.assertEqual(self.console_transport.value(), 'foo\n')
        return d
