#!/usr/bin/env bash

cleanup() {
    rv=$?
    # on exit code 1 this is normal (some tests failed), do not stop the build
    if [ "$rv" = "1" ]; then
        exit 0
    else
        exit $rv
    fi
}

trap "cleanup" INT TERM EXIT

#if hash pytest 2>/dev/null; then
#    echo "pytest found"
#else
#    echo "pytest not found. Trying py.test"
#fi

# First the raw for coverage
echo -e "\n\n****** Running tests ******\n\n"
if [ "${TRAVIS_PYTHON_VERSION}" = "3.5" ]; then
   # full. add the ci_tools/ to path so that the conftest.py is found.
   export PATH=${TRAVIS_BUILD_DIR}/ci_tools/:${PATH}
   echo $PATH
   python -m pytest --junitxml=reports/junit/junit.xml --html=reports/junit/report.html --cov-report term-missing --cov=./valid8 -v valid8/tests/
else
   # faster - skip coverage and html report
   python -m pytest --junitxml=reports/junit/junit.xml -v valid8/tests/
fi