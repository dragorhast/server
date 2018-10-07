import os

from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), "readme.md"), "r") as fh:
    long_description = fh.read()

setup(
    name='server',
    version='1.0.0',
    url='https://github.com/arlyon/dragorhast',
    license='MIT',
    author='arlyon',
    author_email='arlyon@me.com',
    description='todo',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    py_modules=['server'],
    install_requires=[
        'aiohttp',
        'uvloop',
        'aiobreaker'
    ],
    tests_require=[
        'pytest',
    ],
    entry_points='''
        [console_scripts]
        server=server.__main__:run
    ''',
)
