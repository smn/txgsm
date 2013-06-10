txgsm
=====

Utilities for talking to a GSM modem over USB via AT commands.
Will NOT work with all modems, YMMV.

::

    $ virtualenv ve
    (ve)$ pip install .
    (ve)$ twistd txgsm --help
    (ve)$ python ve/bin/twistd -n txgsm --device=/dev/tty.Bluetooth-Modem
