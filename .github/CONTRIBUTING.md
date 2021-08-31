Guidelines for contributing to ue4-docker
=========================================


## Contents

- [Creating issues](#creating-issues)
- [Creating pull requests](#creating-pull-requests)


## Creating issues

When creating an issue to report a bug, please follow the provided issue template. Make sure you include the full output of the `ue4-docker info` command in the provided section, as well as the full output of the `ue4-docker build` command and the command line parameters used to invoke the build if you are reporting a problem with building the container images.

If you are creating an issue for a feature request, you can disregard the default issue template. However, please make sure you have thoroughly read [the documentation](https://docs.adamrehn.com/ue4-docker/) to ensure the requested feature does not already exist before creating an issue.


## Creating pull requests

Before creating a pull request, please ensure sure you have tested your changes on all platforms to which the change applies (Linux / Windows Server / Windows 10 / macOS).

## Autoformatting your changes

ue4-docker uses [Black](https://github.com/psf/black) for its code formatting.
If you are submitting changes, make sure to install and run Black:

- `pip install --user black`
- `black .` (invoked in repository root)
- Now your code is properly formatted
