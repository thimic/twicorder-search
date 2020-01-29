#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import setuptools

from git import Repo
from packaging import version


def get_release_version_from_tag():
    repo = Repo()
    pattern = re.compile(r'v(?P<version>\d+\.\d+\.\d+)')
    versions = [
        pattern.match(t.name).groupdict().get('version') for t in repo.tags
        if pattern.match(t.name)
    ]
    if not versions:
        raise RuntimeError('No git tags found!')
    versions.sort(key=lambda x: version.parse(x))
    return versions[-1]


VERSION = get_release_version_from_tag()


with open('README.md', 'r') as fh:
    LONG_DESCRIPTION = fh.read()


setuptools.setup(
    name='twicorder-search',
    version=VERSION,
    author='Michael Thingnes',
    author_email='thimic@gmail.com',
    description='A Twitter crawler for Python 3 based on Twitter\'s public API',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    url='https://github.com/thimic/twicorder-search',
    packages=['twicorder', 'twicorder/queries'],
    scripts=['bin/twicorder', 'bin/twiread'],
    python_requires='>=3.7',
    setup_requires=['wheel', 'pyyaml'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    license='MIT',
    download_url=(
        f'https://github.com/thimic/twicorder-search/archive/v{VERSION}.tar.gz'
    ),
    keywords=['TWITTER', 'CRAWLER', 'RESEARCH'],
    install_requires=[
        'click',
        'pymongo',
        'pyyaml',
        'requests',
    ],
)
