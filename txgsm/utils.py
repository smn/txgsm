# -*- test-case-name: txgsm.tests.test_utils -*-

from twisted.protocols.basic import LineReceiver

from os import linesep


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
        for item in resp:
            if not item.startswith('+CUSD'):
                continue

            ussd_resp = item.lstrip('+CUSD: ')
            operation = ussd_resp[0]
            content = ussd_resp[3:-4]
            return int(operation), content

    def on_input(self, line):
        d = self.modem.send_command('AT+CUSD=1,"%s",15' % (quote(line),),
                                    expect="+CUSD")
        d.addCallback(self.handle_response)
        return d

    def handle_response(self, result):
        operation, content = self.parse_ussd_response(result['response'])
        self.sendLine(content)
        if operation == self.FURTHER_ACTION:
            return self.prompt()
        else:
            return self.on_exit(operation)
