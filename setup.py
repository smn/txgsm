from setuptools import setup


def requirements(filename):
    return filter(None, open(filename, 'r').read().split('\n'))


def install_requires(filename):
    return [r for r in requirements(filename) if not r.startswith('http')]


def dependency_links(filename):
    return [r for r in requirements(filename) if r.startswith('http')]

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
    install_requires=install_requires('requirements.pip'),
    dependency_links=dependency_links('requirements.pip'),
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
