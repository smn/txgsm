# -*- test-case-name: txgsm.tests.test_utils -*-

import re
from os import linesep

from twisted.protocols.basic import LineReceiver


def quote(s):
    return s.replace('"', '\"')


class Console(LineReceiver):
    delimiter = linesep

    def __init__(self, on_input, prefix=''):
        self.prefix = prefix
        self.on_input = on_input

    def prompt(self):
        self.transport.write("%s> " % (self.prefix,))

    def lineReceived(self, line):
        return self.on_input(line)


class USSDConsole(Console):

    NO_FURTHER_ACTION = 0
    FURTHER_ACTION = 1
    NETWORK_TERMINATED = 2
    OTHER_CLIENT_RESPONDED = 3
    OPERATION_NOT_SUPPORTED = 4
    NETWORK_TIMEOUT = 5

    def __init__(self, modem, on_exit):
        Console.__init__(self, self.on_input, prefix='USSD ')
        self.modem = modem
        self.on_exit = on_exit

    def dial(self, number):
        d = self.modem.dial_ussd_code(number)
        d.addCallback(self.handle_response)
        return d

    def parse_ussd_response(self, resp):
        ussd_resp = resp.lstrip('+CUSD: ')
        operation = ussd_resp[0]
        content = ussd_resp[3:-4]
        return int(operation), content

    def on_input(self, line):
        d1 = self.modem.trigger(r'\+CUSD')
        d1.addCallback(self.handle_response)

        d2 = self.modem.send_command('AT+CUSD=1,"%s",15' % (quote(line),),
                                    pattern=re.compile(r"\+CUSD"))
        d2.addCallback(lambda *a: d1)
        return d2

    def handle_response(self, result):
        operation, content = self.parse_ussd_response(result)
        self.sendLine(content)
        if operation == self.FURTHER_ACTION:
            return self.prompt()
        else:
            return self.on_exit(operation)
