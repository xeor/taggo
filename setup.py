#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

# put package requirements here
requirements = [
    'jmespath',
    'python-box'
]

# Optional packages
extras = {
    'all': ['piexif', 'filetype']
}

# put setup requirements (distutils extensions, etc.) here
setup_requirements = [
    'pytest-runner',
]

# put package test requirements here
test_requirements = [
    'pytest',
    'pytest-catchlog',
    'piexif',
    'filetype',
    'jmespath',
    'python-box'
]

setup(
    name='taggo',
    version='0.14.3',
    description="Tag organizer that creates symlinks from filename-tags",
    long_description=readme + '\n\n' + history,
    author="Lars Solberg",
    author_email='lars.solberg@gmail.com',
    url='https://github.com/xeor/taggo',
    packages=find_packages(include=['taggo'], exclude=['tests']),
    include_package_data=True,
    install_requires=requirements,
    extras_require=extras,
    license="MIT license",
    zip_safe=False,
    keywords='taggo',
    entry_points={
        'console_scripts': [
            'taggo = taggo:main',
        ]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Filesystems',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
