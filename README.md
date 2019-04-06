# toggl2pl

Python module and tool to simplify import of time entries from [Toggl][toggl]
into [PL][pl] (Project Laboratory).

- [Requirements](#requirements)
- [Usage](#usage)
  - [Installation](#installation)
    - [Production](#production)
      - [System packages](#system-packages)
      - [Python module](#python-module)
    - [Development](#development)
  - [Command line interface](#command-line-interface)
    - [Configuration](#configuration)
    - [Examples](#examples)
      - [Simple](#simple)
      - [Rounding](#rounding)
      - [Custom date](#custom-date)
- [Functional](#functional)
  - [Core functional](#core-functional)
  - [Features](#features)
- [Roadmap](#roadmap)
- [Internals](#internals)
  - [Supported APIs](#supported-apis)
  - [Build application](#build-application)

## Requirements

The module is written in pure Python and its work verified with Python `3.x`.

As far as there are no low-level system calls (at least now) the module should
be platform independent, i.e. work on any platform where Python is available.

_Python `2.7` (and older) support is not planned since Python `2.7` will not be
maintained past January 1, 2020._

## Usage

### Installation

#### Production

##### System packages

The application is distributing for Linux and Windows systems as single statically
compiled executable files packaged in ZIP archives and signed with GPG key.

Example installation steps to execute on Linux:

```bash
unzip toggl2pl-1.0.0-linux-amd64.zip
install -v -D toggl2pl ~/.local/bin/toggl2pl
rm -fv toggl2pl-1.0.0-linux-amd64.zip toggl2pl
```

Verify application work with your Linux distribution:

```bash
toggl2pl --help
```

##### Python module

In case you need to install the application as a Python module (for example, you
want to use its API in your new awesome module or application), please follow
the next common Python modules manual installation steps:

1. Obtain the package sources and change working directory to the root of project.
For example, clone the project using Git:

```bash
git clone https://git-y.yourserveradmin.com/pa/toggl2pl.git
cd toggl2pl
```

2. Depending on your use case you may want to install the package into virtual
Python environment instead of modify the system root file system. Please, refer
to the [Development](#development) section for details about `virtualenv` usage.

3. The last step is to install the package data into your environment:

```bash
python setup.py install
```

The command above will build and install package data into correct directories,
so you will be able to access module API from your code and execute scripts
distributed with this module without any `PATH` modifications.

#### Development

The Python `virtualenv` module is recommended to start using the package in
development mode, i.e. without module installation into the system. Please, see
`virtualenv` package installation instructions for some common used operating
systems below.

Fedora 29:

```bash
dnf --assumeyes install python-virtualenv python3-virtualenv
```

Ubuntu 18:

```bash
apt --assume-yes install python-virtualenv python3-virtualenv
```

Once the `virtualenv` package is installed, just create a new Python virtual
environment anywhere you want. The example below assumes virtual environment is
deployed into the root of the cloned project repository:

```bash
virtualenv venv
source venv/bin/activate
pip install --requirement requirements.txt
```

In case of no issues with Python virtual environment setup, now you should be
able to try using the module. In order to check environment, just try to execute
the next CLI command:

```bash
cp -av scripts/toggl2pl toggl2pl.py
./toggl2pl.py --help
```

In the output you will see usage instructions and some CLI arguments descriptions.

In order to interact with time trackers some additional configuration is needed,
please proceed with [Configuration](#configuration) paragraph to start using the
module in command line mode.

### Command line interface

#### Configuration

By default CLI uses configuration file stored as `~/.toggl2pl/config.yml`. Please
execute the next commands to install [config.yml.example](_static/config.yml.example)
as the default configuration file:

```bash
install -v -D docs/_static/config.yml.example ~/.toggl2pl/config.yml
```

Please open the newly created configuration file with your preferable text editor,
read comments and update empty fields with your personal information.

#### Examples

Please note, that currently all CLI flags can be combined into the single command
and examples below just needed to describe flags purposes.

##### Simple

In order to post hours for the current day AS IS just call the script without
any arguments:

```bash
toggl2pl
```

In the output you will see a table with list of projects, tasks and time (real
and rounded) spent on each task. Also you will be prompted to export data to PL
or interrupt export.

##### Rounding

By default, the real number of minutes will be posted to PL. Use rounding or not
depends on your case and team agreement, so please keep this in mind.

In order to post rounded number of minutes - just append `--round` flag to the
script:

```bash
toggl2pl --round
```

The output will be the same, but after confirmation rounded number of time will
be posted to PL instead of real.

_Note: The most actual information about the rounding base value can be found in
the CLI help output._

##### Custom date

In case you need to export Toggl information from the past days, please use the
`--date` flag with exact date in `YYYY-MM-DD` format:

```bash
toggl2pl --date 2016-02-29
```

This will export Toggl time entries dated `2016-02-29` to PL with the same day
and cause **date change request**, so please be aware.

## Functional

### Core functional

The core (minimal) set of features required to start from something is:

* [x] ability to synchronize Toggl clients and projects with PL database.
* [x] ability to export records from Toggl to PL with a minimal human involvement.

### Features

The list of features is not yet ready, but the next helpers already implemented:

- all posts use about the same format (for sure, it is impossible to predict all
  possible cases, but at least common things can and already partially done).
- posts time can be optionally rounded by using internally discussed rules.

## Roadmap

There is a high-level implementation plan which may change with time depending
on external factors and ideas:

* [x] create a minimal set of logic to implement the core functional.
* [x] create command line interface to use already implemented logic.
* [x] tune output format and information to make it useful and easy to understand.
* [x] compile Python code to statically linked executable file to avoid dependency
on Python itself and its modules.
* [x] automate build of Linux executable file to start distributing the tool in
acceptable way.
* [x] automate build of Windows executable file to provide an ability to use the
tool on this platform.
* [x] document existing code, CLI flags and configuration options with Sphinx.
* [ ] freeze existing functional and tweak code to resolve regressions and improve
quality.
* [ ] unit tests and coverage reports for existing minimal set of features.

The list above is incomplete, because there are too many ideas and features which
can be implemented, for example:

- extend the list of [supported APIs](#supported-apis) by [Clockify][clockify]
API in order to provide an alternative to [Toggl][toggl].
- use, for example, Flask, move logic to centralized server and communicate with
it by using HTTP API with a minimal set of required options. But, at the same time
keep ability to use the module in server-less mode and directly communicate with
Toggl and PL API.
- use Elasticsearch with Kibana to store and visualize data passed through server
to provide flexible reports and analytic mechanisms (for each user and for teams).

## Internals

### Supported APIs

The module is designed to work with time trackers over HTTP API, so in case of
any questions, please refer to their official documentation in the first place:

* [x] [Project Laboratory API Documentation][pl_api_docs]
* [x] [Toggl API Documentation][toggl_api_docs]
* [ ] [Clockify API Documentation][clockify_api_docs]

_Note: work on Clockify API support is planned, but not started yet._

### Build application

__Please, make sure you completed with steps described in the [Development](#development)
section before continue with application build, since development environment is
required option on this stage.__

In order to make the application easy distributable and simple to install, the
project code needs to be compiled into the single executable file with all its
dependencies.

While there is a number of tools which may create such kind of distributions,
this project uses [PyInstaller][pyinstaller] which does exactly what is needed
almost out of the box:

```bash
pyinstaller --onefile scripts/toggl2pl
```

The command above will collect all package dependencies and files into the single
executable file which can be distributed to end users without additional actions
on their side (system / Python packages installation).

[clockify]: https://clockify.me/
[clockify_api_docs]: https://clockify.github.io/clockify_api_docs/
[PyInstaller]: https://www.pyinstaller.org/
[pl]: https://pl.itcraft.co/
[pl_api_docs]: https://pl.itcraft.co/api/docs
[toggl]: https://toggl.com/
[toggl_api_docs]: https://github.com/toggl/toggl_api_docs/
