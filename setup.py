from setuptools import setup

import re


def listify(filename):
    return filter(None, open(filename, 'r').read().split('\n'))


_SIMPLE_VERSION_RE = re.compile("(?P<name>.*)-(?P<version>[0-9.]+|dev)$")


def parse_requirements(filename):
    install_requires = []
    dependency_links = []
    for requirement in listify(filename):
        if requirement.startswith("#"):
            continue
        if requirement.startswith("-e"):
            continue
        if requirement.startswith("https:") or requirement.startswith("http:"):
            (_, _, name) = requirement.partition('#egg=')
            ver_match = _SIMPLE_VERSION_RE.match(name)
            if ver_match:
                # egg names with versions need to be converted to
                # an == requirement.
                name = "%(name)s==%(version)s" % ver_match.groupdict()
            install_requires.append(name)
            dependency_links.append(requirement)
        else:
            install_requires.append(requirement)
    return install_requires, dependency_links

install_requires, dependency_links = parse_requirements("requirements.pip")

setup(
    name="txgsm",
    version="0.1.2",
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
    },
    include_package_data=True,
    install_requires=install_requires,
    dependency_links=dependency_links,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
        'Framework :: Twisted',
    ],
)
