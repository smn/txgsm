txgsm
=====

Utilities for talking to a GSM modem over USB via AT commands.
Will NOT work with all modems, YMMV.

::

    $ virtualenv ve
    (ve)$ pip install .
    (ve)$ twistd txgsm --help

Sending an SMS
--------------

Supports multipart & unicode.

::


    (ve)$ twistd -n txgsm --device=/dev/tty.usbmodem1421 \
    > send-sms --to-addr=2776XXXXXXX --message='hello world'
    2013-06-15 11:21:01+0200 [-] Log opened.
    2013-06-15 11:21:01+0200 [-] twistd 13.0.0 (/Users/sdehaan/Documents/Repositories/txgsm/ve/bin/python 2.7.2) starting up.
    2013-06-15 11:21:01+0200 [-] reactor class: twisted.internet.selectreactor.SelectReactor.
    2013-06-15 11:21:01+0200 [-] Connection made
    2013-06-15 11:21:01+0200 [-] Sending: 'AT+CMGF=0'
    2013-06-15 11:21:01+0200 [-] Received: ['OK']
    2013-06-15 11:21:01+0200 [-] Sending: 'ATE0'
    2013-06-15 11:21:01+0200 [-] Received: ['OK']
    2013-06-15 11:21:01+0200 [-] Sending: 'AT+CMEE=1'
    2013-06-15 11:21:01+0200 [-] Received: ['OK']
    2013-06-15 11:21:01+0200 [-] Sending: 'AT+WIND=0'
    2013-06-15 11:21:01+0200 [-] Received: ['OK']
    2013-06-15 11:21:01+0200 [-] Sending: 'AT+CSMS=1'
    2013-06-15 11:21:01+0200 [-] Received: ['+CSMS: 1,1,1', 'OK']
    2013-06-15 11:21:01+0200 [-] Sending: 'AT+CMGS=23'
    2013-06-15 11:21:01+0200 [-] Received: ['> ']
    2013-06-15 11:21:01+0200 [-] Sending: '0001000B817267443908F600000BE8329BFD06DDDF723619\x1a'
    2013-06-15 11:21:04+0200 [-] Received: ['+CMGS: 198', 'OK']
    2013-06-15 11:21:04+0200 [-] Main loop terminated.
    2013-06-15 11:21:04+0200 [-] Server Shut Down.
    $

Interacting with a USSD Service
-------------------------------

::

    (ve)$ twistd -n txgsm --device=/dev/tty.usbmodem1421 \
    > ussd-session --code='*100#'
    2013-06-15 13:42:17+0200 [-] Log opened.
    2013-06-15 13:42:17+0200 [-] twistd 13.0.0 (/Users/sdehaan/Documents/Repositories/txgsm/ve/bin/python 2.7.2) starting up.
    2013-06-15 13:42:17+0200 [-] reactor class: twisted.internet.selectreactor.SelectReactor.
    2013-06-15 13:42:17+0200 [-] Connection made
    2013-06-15 13:42:17+0200 [-] Sending: 'AT+CMGF=0'
    2013-06-15 13:42:18+0200 [-] Received: ['OK']
    2013-06-15 13:42:18+0200 [-] Sending: 'ATE0'
    2013-06-15 13:42:18+0200 [-] Received: ['OK']
    2013-06-15 13:42:18+0200 [-] Sending: 'AT+CMEE=1'
    2013-06-15 13:42:18+0200 [-] Received: ['OK']
    2013-06-15 13:42:18+0200 [-] Sending: 'AT+WIND=0'
    2013-06-15 13:42:18+0200 [-] Received: ['OK']
    2013-06-15 13:42:18+0200 [-] Sending: 'AT+CSMS=1'
    2013-06-15 13:42:18+0200 [-] Received: ['+CSMS: 1,1,1', 'OK']
    2013-06-15 13:42:18+0200 [-] Sending: 'AT+CUSD=1,"*100#",15'
    2013-06-15 13:42:18+0200 [-] Received: ['OK']
    2013-06-15 13:42:18+0200 [-] r ['OK']
    2013-06-15 13:42:23+0200 [-] Unsollicited response: '\r\n+CUSD: 2,"Your balance is R48.70. Out of Airtime? Dial *111# for Airtime Advance. T&Cs apply.",255\r\n'
