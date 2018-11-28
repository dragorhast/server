Style Guide
===========

The code should conform to PEP8_, which is the official python style guide. There is a linter that will report on errors
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


.. _PEP8: https://pep8.org/