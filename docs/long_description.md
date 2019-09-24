# python-validate (valid8)

[![Python versions](https://img.shields.io/pypi/pyversions/valid8.svg)](https://pypi.python.org/pypi/valid8/) [![Build Status](https://travis-ci.org/smarie/python-valid8.svg?branch=master)](https://travis-ci.org/smarie/python-valid8) [![Tests Status](https://smarie.github.io/python-valid8/junit/junit-badge.svg?dummy=8484744)](https://smarie.github.io/python-valid8/junit/report.html) [![codecov](https://codecov.io/gh/smarie/python-valid8/branch/master/graph/badge.svg)](https://codecov.io/gh/smarie/python-valid8)

[![Documentation](https://img.shields.io/badge/doc-latest-blue.svg)](https://smarie.github.io/python-valid8/) [![PyPI](https://img.shields.io/pypi/v/valid8.svg)](https://pypi.python.org/pypi/valid8/) [![Downloads](https://pepy.tech/badge/valid8)](https://pepy.tech/project/valid8) [![Downloads per week](https://pepy.tech/badge/valid8/week)](https://pepy.tech/project/valid8) [![GitHub stars](https://img.shields.io/github/stars/smarie/python-valid8.svg)](https://github.com/smarie/python-valid8/stargazers)


*"valid8ing is not a crime" ;-)*

`valid8` provides user-friendly tools for 3 kind of "entry points":

 * general-purpose **inline** validation (=anywhere in your code), 
 * **function** inputs/outputs validation 
 * **class fields** validation.

All these entry points raise consistent `ValidationError` including user-friendly details, with inheritance of `ValueError` / `TypeError` as appropriate. You can **customize this error** so as to get unique error types convenient for i18n.

The documentation for users is available here: [https://smarie.github.io/python-valid8/](https://smarie.github.io/python-valid8/)

A readme for developers is available here: [https://github.com/smarie/python-valid8](https://github.com/smarie/python-valid8)
