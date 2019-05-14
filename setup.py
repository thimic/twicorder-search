#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from distutils.core import setup


setup(
    name='twicorder-search',
    packages=['twicorder', 'twicorder/queries'],
    scripts=['bin/twicorder', 'bin/twiread'],
    version='0.2.6',
    license='MIT',
    description='A Twitter crawler for Python 3 based on Twitter\'s public API',
    author='Michael Thingnes',
    author_email='thimic@gmail.com',
    url='https://github.com/thimic/twicorder-search',
    download_url=(
        'https://github.com/thimic/twicorder-search/archive/v0.2.6.tar.gz'
    ),
    keywords=['TWITTER', 'CRAWLER', 'RESEARCH'],
    install_requires=[
        'click',
        'pymongo',
        'pyyaml',
        'requests',
        'requests_oauthlib',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

