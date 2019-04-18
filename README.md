# python-validate (valid8)

*"valid8ing is not a crime" ;-)*

[![Python versions](https://img.shields.io/pypi/pyversions/valid8.svg)](https://pypi.python.org/pypi/valid8/) [![Build Status](https://travis-ci.org/smarie/python-valid8.svg?branch=master)](https://travis-ci.org/smarie/python-valid8) [![Tests Status](https://smarie.github.io/python-valid8/junit/junit-badge.svg?dummy=8484744)](https://smarie.github.io/python-valid8/junit/report.html) [![codecov](https://codecov.io/gh/smarie/python-valid8/branch/master/graph/badge.svg)](https://codecov.io/gh/smarie/python-valid8)

[![Documentation](https://img.shields.io/badge/doc-latest-blue.svg)](https://smarie.github.io/python-valid8/) [![PyPI](https://img.shields.io/pypi/v/valid8.svg)](https://pypi.python.org/pypi/valid8/) [![Downloads](https://pepy.tech/badge/valid8)](https://pepy.tech/project/valid8) [![Downloads per week](https://pepy.tech/badge/valid8/week)](https://pepy.tech/project/valid8) [![GitHub stars](https://img.shields.io/github/stars/smarie/python-valid8.svg)](https://github.com/smarie/python-valid8/stargazers)

`valid8` provides user-friendly tools for 

 * general-purpose inline validation, 
 * function inputs/outputs validation 
 * class fields validation. 
 
All entry points raise consistent `ValidationError` including all contextual details, with dynamic inheritance of `ValueError`/`TypeError` as appropriate. Originally from the [autoclass](https://smarie.github.io/python-autoclass/) project.

**This is the readme for developers.** The documentation for users is available here: [https://smarie.github.io/python-valid8/](https://smarie.github.io/python-valid8/)

## Want to contribute ?

Contributions are welcome ! Simply fork this project on github, commit your contributions, and create pull requests.

Here is a non-exhaustive list of interesting open topics: [https://github.com/smarie/python-valid8/issues](https://github.com/smarie/python-valid8/issues)

## Installing all requirements

In order to install all requirements, including those for tests and packaging, use the following command:

```bash
pip install -r ci_tools/requirements-pip.txt
```

## Running the tests

This project uses `pytest`.

```bash
pytest -v valid8/tests/
```

## Packaging

This project uses `setuptools_scm` to synchronise the version number. Therefore the following command should be used for development snapshots as well as official releases: 

```bash
python setup.py egg_info bdist_wheel rotate -m.whl -k3
```

## Generating the documentation page

This project uses `mkdocs` to generate its documentation page. Therefore building a local copy of the doc page may be done using:

```bash
mkdocs build -f docs/mkdocs.yml
```

## Generating the test reports

The following commands generate the html test report and the associated badge. 

```bash
pytest --junitxml=junit.xml -v valid8/tests/
ant -f ci_tools/generate-junit-html.xml
python ci_tools/generate-junit-badge.py
```

### PyPI Releasing memo

This project is now automatically deployed to PyPI when a tag is created. Anyway, for manual deployment we can use:

```bash
twine upload dist/* -r pypitest
twine upload dist/*
```

### Merging pull requests with edits - memo

Ax explained in github ('get commandline instructions'):

```bash
git checkout -b <git_name>-<feature_branch> master
git pull https://github.com/<git_name>/python-valid8.git <feature_branch> --no-commit --ff-only
```

if the second step does not work, do a normal auto-merge (do not use **rebase**!):

```bash
git pull https://github.com/<git_name>/python-valid8.git <feature_branch> --no-commit
```

Finally review the changes, possibly perform some modifications, and commit.
