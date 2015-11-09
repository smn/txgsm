txgsm
=====

txgsm provides utilities for talking to a GSM modem via AT commands.

Installation
------------

Install txgsm from PyPi directly::

  pip install txgsm

Or checkout the source from Github::

  git clone https://github.com/smn/txgsm.git

And install the dependencies::

  pip install -r requirements.txt
  pip install -r requirements-dev.txt
  pip install -e .

Usage
-----

Probe the modem ``/dev/tty.usbmodem1421`` to see if it is something modem-ish::

  twistd -n txgsm --device=/dev/tty.usbmodem1421 probe-modem

To check other options::

  twistd -n txgsm --help

Supported modems
----------------

The following modem backends are included:

============================================  =========================
Modem                                         Backend
============================================  =========================
`3G dongle for Vodacom`_                      ``txgsm.backend.foo``
`Truteq's GSM CommServ`_                      ``txgsm.backend.bar``
`Raspberry PI SIM800 GSM/GPRS Add-on V2.0`_   ``txgsm.backend.spam``
============================================  =========================

Pull requests for new backends are very welcome!

Tests
-----

You can run the tests using ``trial``::

  trial txgsm

Or using ``py.test`` (that also generates a test coverage report)::

  py.test --cov=txgsm --cov-report=term


.. toctree::
   :maxdepth: 2


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _3G dongle for Vodacom: http://www.imei.info/phonedatabase/11862-zte-vodafone-k3772-z/
.. _Truteq's GSM CommServ: http://www.truteqdevices.com/products/wireless-server-solutions/commserver-v5/
.. _Raspberry PI SIM800 GSM/GPRS Add-on V2.0: http://wiki.iteadstudio.com/RPI_SIM800_GSM/GPRS_ADD-ON_V2.0
