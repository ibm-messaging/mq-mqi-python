# Release

GitHub Action is used to build the release files and publish them on PyPi.
This is automatically triggered when a new tag is created.


## Pre-release steps

* Create a new branch with a name that starts with `release-`.
  Ex: `release-2.1.0`
* Update the version inside setup.py
* Update CHANGELOG.md with the latest version and release date.
  Add a note to the IBM MQ C Redistributables version used for this release.
* Create a pull request and make sure all checks pass.
  The wheels are generated as part of the PR checks,
  but they are not yet published to PyPI.


## Release steps

* Use [GitHub Release](https://github.com/ibm-messaging/mq-mqi-python/releases/new) to create a new release together with a new tag.
* You don't have to create a GitHub Release, the important part is to
  create a new tag.
* The tag value is the version. Without any prefix.
* Once a tag is pushed to the repo, GitHub Action will re-run all the jobs
  and will publish to PyPI.


## Post-release steps

* Update the version inside setup.py to the next development version.
  Increment the micro version and add a .dev0 suffix.
* Merge the pull request
