#!/usr/bin/env python

# Project skeleton maintained at https://github.com/jaraco/skeleton

import io

import setuptools

with io.open('README.rst', encoding='utf-8') as readme:
	long_description = readme.read()

name = 'jaraco.pmxbot'
description = 'pmxbot commands by jaraco'

params = dict(
	name=name,
	use_scm_version=True,
	author="Jason R. Coombs",
	author_email="jaraco@jaraco.com",
	description=description or name,
	long_description=long_description,
	url="https://github.com/jaraco/" + name,
	packages=setuptools.find_packages(exclude='tests'),
	include_package_data=True,
	namespace_packages=name.split('.')[:-1],
	install_requires=[
		'twilio',
		'cherrypy_cors',
		'jaraco.itertools',
	],
	extras_require={
	},
	setup_requires=[
		'setuptools_scm>=1.15.0',
	],
	classifiers=[
		"Development Status :: 5 - Production/Stable",
		"Intended Audience :: Developers",
		"License :: OSI Approved :: MIT License",
		"Programming Language :: Python :: 3",
	],
	entry_points={
		'pmxbot_handlers': [
			'jaraco.pmxbot = jaraco.pmxbot',
			'http API = jaraco.pmxbot.http',
			'notification = jaraco.pmxbot.notification',
		],
	},
)
if __name__ == '__main__':
	setuptools.setup(**params)
