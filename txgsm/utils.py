from twisted.protocols.basic import LineReceiver
from os import linesep


class Console(LineReceiver):
    delimiter = linesep

    def __init__(self, on_input, prefix=''):
        self.prefix = prefix
        self.on_input = on_input

    def prompt(self):
        self.transport.write("%s> " % (self.prefix,))

    def lineReceived(self, line):
        self.prompt()
        return self.on_input(self, line)
