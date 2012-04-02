#!/usr/bin/env python
# Generated by jaraco.develop (https://bitbucket.org/jaraco/jaraco.develop)
import setuptools

setup_params = dict(
	name='jaraco.pmxbot',
	use_hg_version=True,
	author="Jason R. Coombs",
	author_email="jaraco@jaraco.com",
	url="https://bitbucket.org/jaraco/jaraco.pmxbot",
	packages=setuptools.find_packages(),
	namespace_packages=['jaraco'],
	zip_safe=False,
	setup_requires=[
		'hgtools',
	],
)
if __name__ == '__main__':
	setuptools.setup(**setup_params)
