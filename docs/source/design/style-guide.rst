Style Guide
===========

The code should conform to PEP8_, the official python style guide. There is a linter that will report on errors
in the style, which will improve conformity. To access it, run the following command:

>>> pylint server
Your code has been rated at 8.03/10 (previous run: 7.40/10, +0.63)


It will spit out a bunch of "problems", and give your code a rating. Make sure it goes up most times you write code, and
we'll be okay. The rules might be relaxed later on, but it's a good way to understand what code should look like. It is
only a guidance, not the source of truth.

Some quick pointers:

* always use descriptive names
* use snake_case for naming
* 4 spaces to an indent, no tabs
* 120 character width
* CMD + ALT + L will automatically format the current document
* Committing code through PyCharm allows you to automatically format every file you've edited

Versioning
----------

The server uses semantic versioning as defined in PEP440_. When a new version is built, the version number is incremented
in :data:`server.version` and a git tag with the desired version number is added to the commit. This is typically done
as part of a new PR before it is merged or, alternatively, straight to the master branch.

Semantic versioning is done with a very simple scheme. The version is defined by a string of the format `a.b.c` where:

- 'a' denotes a major (potentially breaking) version
- 'b' denotes a minor version with added features
- 'c' denotes a bug fix patch

Additionally, it is possible to append alpha, beta, and release candidate segments, suffixed with 'a', 'b', or 'rc'.
Each major, minor, or patch version can increment indefinitely as needed.

Some examples of valid formats are listed below:

- 0.1.0
- 0.3.4
- 1.0.0b3
- 1.10.3
- 2.0.0rc1

Documentation
-------------

Try to use `Semantic Line Breaks`_ when possible when writing documentation that will frequently change.



.. _PEP8: https://www.python.org/dev/peps/pep-0008/
.. _PEP440: https://www.python.org/dev/peps/pep-0440/
.. _`Semantic Line Breaks`: http://sembr.org/