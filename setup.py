from os.path import abspath, dirname, join
from setuptools import setup

# Read the README markdown data from README.md
with open(abspath(join(dirname(__file__), "README.md")), "rb") as readmeFile:
    __readme__ = readmeFile.read().decode("utf-8")

# Read the version number from version.py
with open(abspath(join(dirname(__file__), "ue4docker", "version.py"))) as versionFile:
    __version__ = (
        versionFile.read().strip().replace("__version__ = ", "").replace('"', "")
    )

setup(
    name="ue4-docker",
    version=__version__,
    description="Windows and Linux containers for Unreal Engine 4",
    long_description=__readme__,
    long_description_content_type="text/markdown",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Build Tools",
        "Environment :: Console",
    ],
    keywords="epic unreal engine docker",
    url="http://github.com/adamrehn/ue4-docker",
    author="Adam Rehn",
    author_email="adam@adamrehn.com",
    license="MIT",
    packages=[
        "ue4docker",
        "ue4docker.diagnostics",
        "ue4docker.exports",
        "ue4docker.infrastructure",
    ],
    zip_safe=False,
    python_requires=">=3.6",
    install_requires=[
        "colorama",
        "container-utils",
        "docker>=3.0.0",
        "flask",
        "humanfriendly",
        "Jinja2>=2.11.3",
        "packaging>=19.1",
        "psutil",
        "requests",
        "semver>=2.7.9,<3.0.0",
        "setuptools>=38.6.0",
        "termcolor",
        "twine>=1.11.0",
        "wheel>=0.31.0",
    ],
    package_data={
        "ue4docker": [
            "dockerfiles/*/*/.dockerignore",
            "dockerfiles/diagnostics/*/*/*",
            "dockerfiles/*/*/*",
            "tests/*.py",
        ]
    },
    entry_points={"console_scripts": ["ue4-docker=ue4docker:main"]},
)
