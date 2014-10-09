from setuptools import setup

import os
import imp

mod_path = os.path.abspath('capture.py')
mod = imp.load_source('capture', mod_path)
version = mod.__version__


classifiers = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Utilities'
]


setup(
    name='maya-capture',
    version=version,
    description='Playblasting in Maya done right"',
    long_description="Playblasting in Maya done right",
    author='Marcus Ottosson',
    author_email='marcus@abstractfactory.com',
    url='https://github.com/mottosso/maya-capture',
    license="MIT",
    py_modules=["capture"],
    zip_safe=False,
    classifiers=classifiers
)
