#!/usr/bin/env python3

from setuptools import setup
from setuptools import find_packages

setup(
    name='mia',
    version='0.0.2',
    description='MIA - Mission Impossible: Hardening Android for Security and Privacy',
    author='The MIA team',
    url='https://github.com/SchnWalter/mission-impossible-android',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'mia = mia.__main__:main'
        ],
    },
    install_requires=[
        'docopt',
        'PyYAML',
    ],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Operating System :: POSIX',
        'Topic :: Utilities',
    ]
)
