# Dragorhast Server

[![Build Status](https://img.shields.io/travis/dragorhast/server.svg?style=flat-square)](https://travis-ci.org/dragorhast/server)
[![GitHub License](https://img.shields.io/github/license/dragorhast/server.svg?style=flat-square)](https://github.com/dragorhast/server/blob/master/license.md)
![Python Version](https://img.shields.io/badge/python-3.5%2B-blue.svg?style=flat-square)
[![GitHub issues](https://img.shields.io/github/issues/dragorhast/server.svg?style=flat-square)](https://github.com/dragorhast/server/issues)

<p align="center"><img src="./graphic.png" /></p>

The server repository contains the APIs for the other components (mobile app, hardware payload) as well as
the pricing module to determine the correct prices for each rental. This server provides a range of endpoints
that facilitate all the functionality of the app from rental bookings to admin management.

## Installation

Installing the server is easy. Assuming you have a recent version of python (3.5 or above) then

    > git clone https://github.com/dragorhast/server.git
    > cd server
    > pipenv install

Alternatively, for development,

    > pipenv install --dev

## Usage

Running the server, once the requirements are installed, is simple:

    > pipenv run server
    ======== Running on http://0.0.0.0:8080 ========
    (Press CTRL+C to quit)


Then, simply navigate to the API docs to get started.

## Testing

The server is equipped for testing with a range of tools:

1. **pytest:** unit testing
2. **flake8:** simple PEP8 violation checker
3. **pylint:** more in-depth bug checking
4. **mypy:** static type checking
5. **safety:** dependency vulnerability warnings
6. **bandit:** security warnings

You can run the lot like so:

    pipenv run test
    flake8 server
    pylint server
    mypy server
    safety check
    bandit -r server

All code submitted to the repo will have to pass all the tests
on Travis CI before being deployed.

## Tooling

In addition to the CI / CD above, the repository is monitored by a number of tools to automate the development process.
As well as being able to know the build status of any pull request at a glance, we use codecov, hound, and codeclimate
to track various metrics about the history of the codebase such as general code quality, unit test coverage, and design
errors or antipatterns.

1. [**codecov**](https://codeclimate.com/github/dragorhast/server) takes reports generated from the CI process and displays the total coverage as well as the change in
coverage. This is a good way to tell if someone adds a feature with minimal unit testing.
2. **codeclimate** scans the codebase for code smells, complex functions, and other high level problems assigning a
score to the project. We can tell, based on the report generated, if there are any issues with a branch before it is
merged into master.
3. **hound** does automated code review on pull requests to automatically highlight the most obvious errors without
human intervention allowing us to focus on the content itself.

## Documentation

Documentation is included. You may build it by installing the dev dependencies and running `sphinx-autobuild`.

```bash

pipenv install --dev
pipenv run sphinx-autobuild
```
