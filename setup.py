import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='adarnauth-eveonline',
    version='0.1',
    install_requires=[
        'django>=1.10,<2.0',
        'evelink>=0.7.4',
        'celery>=4.0',
        'adarnauth-esi>=1.2.2',
    ],
    packages=find_packages(),
    include_package_data=True,
    license='GNU GPLv3',
    description='A Django app for handling data structures from EVE Online.',
    long_description=README,
    url='https://adarnauth.tech/',
    author='Adarnof',
    author_email='adarnof@gmail.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.9',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU GPLv3',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
