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

    (ve)$ twistd -n txgsm --device=/dev/tty.usbmodem1421 ussd-session --code='*120*8864#'
    2013-06-15 19:14:31+0200 [-] Log opened.
    2013-06-15 19:14:31+0200 [-] twistd 13.0.0 (/Users/sdehaan/Documents/Repositories/txgsm/ve/bin/python 2.7.2) starting up.
    2013-06-15 19:14:31+0200 [-] reactor class: twisted.internet.selectreactor.SelectReactor.
    2013-06-15 19:14:31+0200 [-] Connection made
    2013-06-15 19:14:31+0200 [-] Sending: 'AT+CMGF=0'
    2013-06-15 19:14:31+0200 [-] Received: ['OK']
    2013-06-15 19:14:31+0200 [-] Sending: 'ATE0'
    2013-06-15 19:14:31+0200 [-] Received: ['OK']
    2013-06-15 19:14:31+0200 [-] Sending: 'AT+CMEE=1'
    2013-06-15 19:14:31+0200 [-] Received: ['OK']
    2013-06-15 19:14:31+0200 [-] Sending: 'AT+WIND=0'
    2013-06-15 19:14:31+0200 [-] Received: ['OK']
    2013-06-15 19:14:31+0200 [-] Sending: 'AT+CSMS=1'
    2013-06-15 19:14:31+0200 [-] Received: ['+CSMS: 1,1,1', 'OK']
    2013-06-15 19:14:31+0200 [-] Sending: 'AT+CSQ'
    2013-06-15 19:14:31+0200 [-] Received: ['+CSQ: 12,0', 'OK']
    2013-06-15 19:14:31+0200 [-] Sending: 'AT+CUSD=1,"*120*8864#",15'
    2013-06-15 19:14:35+0200 [-] Received: ['OK', '+CUSD: 1,"What would you like to search Wikipedia for? ",15']
    "What would you like to search Wikipedia for? "
    USSD > HIV
    2013-06-15 19:14:42+0200 [-] Sending: 'AT+CUSD=1,"HIV",15'
    2013-06-15 19:14:46+0200 [-] Received: ['OK', '+CUSD: 1,"1. HIV\n2. HIV/AIDS\n3. HIV/AIDS in China\n4. Diagnosis of HIV/AIDS\n5. History of HIV/AIDS\n6. Circumcision and HIV\n7. AIDS dementia complex\n8. HIV/AIDS in Ukraine ",15']
    "1. HIV
    2. HIV/AIDS
    3. HIV/AIDS in China
    4. Diagnosis of HIV/AIDS
    5. History of HIV/AIDS
    6. Circumcision and HIV
    7. AIDS dementia complex
    8. HIV/AIDS in Ukraine "
    USSD > 1
    2013-06-15 19:14:47+0200 [-] Sending: 'AT+CUSD=1,"1",15'
    2013-06-15 19:14:49+0200 [-] Received: ['OK', '+CUSD: 1,"1. HIV\n2. Virology\n3. Diagnosis\n4. Research\n5. History\n6. Notes\n7. External links ",15']
    "1. HIV
    2. Virology
    3. Diagnosis
    4. Research
    5. History
    6. Notes
    7. External links "
    USSD > 1
    2013-06-15 19:14:57+0200 [-] Sending: 'AT+CUSD=1,"1",15'
    2013-06-15 19:15:01+0200 [-] Received: ['OK', '+CUSD: 2,"Human immunodeficiency virus (HIV) is a lentivirus (slowly replicating retrovirus) that causes acquired immunodeficiency ...\n(Full content sent by SMS.) ",15']
    2013-06-15 19:15:01+0200 [-] Shutting down with: 2
    "Human immunodeficiency virus (HIV) is a lentivirus (slowly replicating retrovirus) that causes acquired immunodeficiency ...
    (Full content sent by SMS.) "
    2013-06-15 19:15:03+0200 [-] Main loop terminated.
    2013-06-15 19:15:03+0200 [-] Server Shut Down.
