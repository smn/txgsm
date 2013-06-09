from setuptools import setup


def listify(filename):
    return filter(None, open(filename, 'r').read().split('\n'))

setup(
    name="txgsm",
    version="0.1",
    url='http://github.com/smn/txgsm',
    license='BSD',
    description="Utilities for talking to a GSM modem over USB via AT "
                "commands.",
    long_description=open('README.rst', 'r').read(),
    author='Simon de Haan',
    author_email='simon@praekeltfoundation.org',
    packages=[
        "txgsm",
        "twisted.plugins",
    ],
    package_data={
        'twisted.plugins': ['twisted/plugins/txgsm_plugin.py'],
        'txgsm.etc': ['txgsm/etc/*']
    },
    include_package_data=True,
    install_requires=listify('requirements.pip'),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
        'Framework :: Twisted',
    ],
)
