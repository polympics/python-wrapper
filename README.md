# Polympics API Python Wrapper

This project is available on PyPI, and can be installed with
```
$ python3 -m pip install polympics
```
(Or the equivalent for however you use pip.)

For instructions on setting the project up for development, see below.

## Setup

This project requires Python3.9+ (Python 4 is not acceptable). Depending on your operating system, you may be able to install it from your package manager, an external PPA (like deadsnakes), or [the official website](https://python.org/download).

This project uses `pipenv` to manage dependencies. To get started, you'll need to install `pipenv` from PyPI, eg:
```bash
$ python3 -m pip install pipenv
```

Once you have `pipenv` installed, you can create a virtual enviroment and install the project's dependencies with
```bash
$ pipenv shell
$ pipenv install
```
To additionally install development dependencies, do
```bash
$ pipenv install -d
```

## Usage

[Docs are available here](https://polympics.github.io/python-wrapper).
