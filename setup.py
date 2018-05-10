#!/usr/bin/env python2

from distutils.core import setup

setup(
	name='ripabook',
	version='0.2',
	license='GPL',
	description='Backend to ripp audiobooks',
	author='Dominik Heidler',
	author_email='dheidler@gmail.com',
	url='http://github.com/asdil12/ripabook',
	packages=['ripabook'],
	scripts=['bin/ripabook'],
)
