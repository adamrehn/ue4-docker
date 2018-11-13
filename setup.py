from os.path import abspath, dirname, join
from setuptools import setup

# Read the version number from version.py
with open(abspath(join(dirname(__file__), 'ue4docker', 'version.py'))) as versionFile:
	__version__ = versionFile.read().strip().replace('__version__ = ', '').replace("'", '')

setup(
	name='ue4-docker',
	version=__version__,
	description='Windows and Linux containers for Unreal Engine 4',
	classifiers=[
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python :: 3.6',
		'Programming Language :: Python :: 3.7',
		'Topic :: Software Development :: Build Tools',
		'Environment :: Console'
	],
	keywords='epic unreal engine docker',
	url='http://github.com/adamrehn/ue4-docker',
	author='Adam Rehn',
	author_email='adam@adamrehn.com',
	license='MIT',
	packages=['ue4docker', 'ue4docker.infrastructure'],
	zip_safe=False,
	python_requires = '>=3.6',
	install_requires = [
		'colorama',
		'docker>=3.0.0',
		'flask',
		'humanfriendly',
		'psutil',
		'semver>=2.7.9',
		'setuptools',
		'termcolor',
		'wheel'
	],
	package_data = {
		'ue4docker': ['dockerfiles/*/*/*']
	},
	entry_points = {
		'console_scripts': ['ue4-docker=ue4docker:main']
	}
)
