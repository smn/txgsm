txgsm
=====

Utilities for talking to a GSM modem over USB via AT commands.
Will NOT work with all modems, YMMV.

|travis|_ |coveralls|_

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

Provide the USSD code you want to dial with ``--code=...``.
Adding ``-v`` or ``--verbose`` to see the AT commands.

::

    (ve)$ twistd -n txgsm --device=/dev/tty.usbmodem1421 ussd-session --code='*120*8864#'
    2013-06-15 19:37:52+0200 [-] Log opened.
    2013-06-15 19:37:52+0200 [-] twistd 13.0.0 (/Users/sdehaan/Documents/Repositories/txgsm/ve/bin/python 2.7.2) starting up.
    2013-06-15 19:37:52+0200 [-] reactor class: twisted.internet.selectreactor.SelectReactor.
    2013-06-15 19:37:52+0200 [-] Connecting to modem.
    2013-06-15 19:37:53+0200 [-] Connected, starting console for: *120*8864#
    2013-06-15 19:37:53+0200 [-] Dialing: *120*8864#
    What would you like to search Wikipedia for?
    USSD > HIV
    1. HIV
    2. HIV/AIDS
    3. HIV/AIDS in China
    4. Diagnosis of HIV/AIDS
    5. History of HIV/AIDS
    6. Circumcision and HIV
    7. AIDS dementia complex
    8. HIV/AIDS in Ukraine
    USSD > 2
    1. HIV/AIDS
    2. Signs and symptoms
    3. Transmission
    4. Virology
    5. Pathophysiology
    6. Diagnosis
    7. Prevention
    8. Management
    9. Prognosis
    10. Epidemiology
    USSD > 1
    Human immunodeficiency virus infection / acquired immunodeficiency syndrome (HIV/AIDS) is a disease of the human immune system ...
    (Full content sent by SMS.)
    2013-06-15 19:38:24+0200 [-] Main loop terminated.
    2013-06-15 19:38:24+0200 [-] Server Shut Down.


.. |travis| image:: https://travis-ci.org/smn/txgsm.png?branch=develop
.. _travis: https://travis-ci.org/smn/txgsm

.. |coveralls| image:: https://coveralls.io/repos/smn/txgsm/badge.png?branch=develop
.. _coveralls: https://coveralls.io/r/smn/txgsm

