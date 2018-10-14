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
    > pip install -e .

## Usage

Running the server, once the requirements are installed, is simple:

    > server
    ======== Running on http://0.0.0.0:8080 ========
    (Press CTRL+C to quit)


Then, simply navigate to the API docs to get started.

## Testing

The server is equipped for testing with a range of tools:

1. **flake8:** simple PEP8 violation checker
2. **pylint:** more in-depth bug checking
3. **tox:** unit testing
4. **mypy:** static type checking
5. **safety:** dependency vulnerability warnings
6. **bandit:** security warnings

To make sure they're all installed, use pip to install the
development requirements:

    pip install -r requirements.txt

Then, you can run the lot like so:

    flake8 server
    pylint server
    mypy server
    tox
    safety check
    bandit -r server

All code submitted to the repo will have to pass all the tests
on Travis CI before being deployed.