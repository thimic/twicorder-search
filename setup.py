#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from distutils.core import setup


setup(
    name='twicorder-search',
    packages=['twicorder-search'],
    version='0.2.0',
    license='MIT',
    description='A Twitter crawler for Python 3 based on Twitter\'s public API',
    author='Michael Thingnes',
    author_email='thimic@gmail.com',
    url='https://github.com/thimic/twicorder-search',
    download_url='https://github.com/thimic/twicorder-search/archive/v_01.tar.gz',
    keywords=['TWITTER', 'CRAWLER', 'RESEARCH'],
    install_requires=[
        'pymongo',
        'pyyaml',
        'requests',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Researchers',
        'Topic :: Research :: Twitter',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)

