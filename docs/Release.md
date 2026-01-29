# Creating and releasing new versions

## Distributions, binary files, wheels and PyPI
For now, only the source distribution gets uploaded to PyPI. Doing a generic wheel that runs on a range of Linux distros
is non-trivial, needing to be built in a special "manylinux" environment.There are some steps described below that start
to automate the process of building and uploading with GitHub actions for some architectures. But it's not ready at the
moment.

I **have** however made the C extension module more agnostic as to the version of Python it's running with. It conforms
to the [Limited API](https://docs.python.org/3/c-api/stable.html#limited-c-api) at the Python 3.9 level. This ought to
make it easier to redistribute applications within your own environment, compiling only once and copying the `.so` file
to other environments with Python 3.9 or newer levels.

### GitHub Action
A [GitHub Action](../.github/workflows/release.yaml) in this repo can be used to build the release files including
binary wheels, but not to actually upload them to PyPI. This is to allow local checks to be done and to fit better with
my own workflows, including use of other PyPI-equivalent servers for testing of the images. The build is triggered
manually with the gh `workflow_dispatch` operation. The workflow configuration file does have some automatic steps (for
example to run on PR creation), but they are commented out. The Redistributable Client packages are used to build binary
wheels for Linux/x64 and Windows.

The Action is not going to be used for a real release for now, as it still requires work to modify it to build
`manylinux` images. The `runActions.sh` script is the piece that can be used to test the flow including downloading the
generated artifacts. It might nonetheless be helpful for populating private PyPI repositories.

### PyPI Servers
The `tools` subdirectory also includes scripts to let you run your own PyPI-equivalent local server, and to upload
binary wheels to that location. See the `testInstServer.sh` and `testInstClient.sh` scripts. They will almost certainly
require modifications for your own systems, but the basic framework is there. This local PyPI server does not have all
the same constraints that the real PyPI has. For example, it doesn't stop you uploading a Linux binary wheel that has
been built outside the "manylinux" framework. Again, that may help with internal distribution of your applications.

## Release Steps
At each of these steps, there are opportunities to test the code/packages in various ways including local and remote
testing on a variety of platforms. Only the final release to PyPI is irrevocable.

### Initial changes
* Use `copyDefs` to get the most recent MQI header files (MQ developers only - requires access to product build machines)
* Update _setup.py_ with new version number
* Update _code/examples/Dockerfile_ and _.github/workflows/release.yaml_ with current MQ VRMF
* Any other code changes
* Use the `check` script to make sure it all looks sensible
* Running `pyRelease.sh -lY` emulates a real release. The local server can be the source of a test environment's
  installations. (The local server by default only permits localhost connections. You'd need to edit the startup script
  to permit wider access.)

### Publish to GitHub
* Commit and push changes
* Create a release tag for the new version number

### Publish to PyPI
* Use `pyRelease.sh` to either build an sdist locally or drive the GitHub Action to build the distribution files (sdist
  and wheels). Any Action-created artifacts are downloaded from GitHub and can then be uploaded after the script asks
  for a final manual confirmation to PyPI. Or to the PyPI Test server (which is the default option) if you prefer.