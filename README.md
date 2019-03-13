# python-toggl2pl

- [Requirements](#requirements)
- [Usage](#usage)
  - [Installation](#installation)
    - [Development](#development)
    - [Production](#production)
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

The project goal is to create simple to use interface to export time tracked with
[Toggl][toggl] into [PL][pl] (Project Laboratory).

## Requirements

The module is written in pure Python and its work verified with Python versions
`2.7` and `3.7`, so it most likely will work with all Python `3.x` versions, but
that is not yet verified.

As far as there are no low-level system calls (at least now) the module should
be platform independent, i.e. work on any platform where Python is available.

## Usage

### Installation

#### Development

The Python `virtualenv` module is recommended to start using the package in
development mode, i.e. without module installation into the system. Please, see
`virtualenv` package installation instructions for some common used operating
systems below.

CentOS 7:

```bash
yum --assumeyes install python-virtualenv
```

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
```

In case of no issues with Python virtual environment setup, now you should be
able to try using the module. In order to check environment, just try to execute
the next CLI command:

```bash
./toggl2pl.py --help
```

In the output you will see usage instructions and some CLI arguments descriptions.

In order to interact with time trackers some additional configuration is needed,
please proceed with [Configuration](#configuration) paragraph to start using the
module in command line mode.

#### Production

While there is no DEB and RPM packages build yet, the only one way to make the
project working locally is to install it as Python module or use `virtualenv` to
create virtual Python environment.

Please see [Development](#development) paragraph for details.

### Command line interface

#### Configuration

By default CLI uses configuration file stored as `~/.toggl2pl/config.yml`. Please
execute the next commands to install [config.yml.example](data/config.yml.example)
as the default configuration file:

```bash
install -v -D data/config.yml.example ~/.toggl2pl/config.yml
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
./toggl2pl.py
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
./toggl2pl.py --round
```

The output will be the same, but after confirmation rounded number of time will
be posted to PL instead of real.

_Note: The most actual information about the rounding base value can be found in
the CLI help output._

##### Custom date

In case you need to export Toggle information from the past days, please use the
`--date` flag with exact date in `YYYY-MM-DD` format:

```bash
./toggl2pl.py --date 2016-02-29
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

### Roadmap

There is a high-level implementation plan which may change with time depending
on external factors and ideas:

* [x] create a minimal set of logic to implement the core functional.
* [x] create command line interface to use already implemented logic.
* [ ] tune output format and information to make it useful and easy to understand.
* [ ] document existing code, CLI flags and configuration options with Sphinx.
* [ ] compile Python code to statically linked executable files (using [cx_Freeze][cx_Freeze]
  or [PyInstaller][PyInstaller]) to avoid dependency on Python itself and its
  modules.
* [ ] automate build of DEB and RPM packages with compiled executable files to
start distributing the module in acceptable way.
* [ ] freeze existing functional and tweak code to resolve regressions and improve
quality.
* [ ] unit tests and coverage reports for existing minimal set of features.

The list above is incomplete, because there are too many ideas and features which
can be implemented, for example:

- use, for example, Flask, move logic to centralized server and communicate with
it by using HTTP API with a minimal set of required options. But, at the same time
keep ability to use the module in server-less mode and directly communicate with
Toggl and PL API.
- use Elasticsearch with Kibana to store and visualize data passed through server
to provide flexible reports and analytic mechanisms (for each user and for teams).

## Internals

The module is designed to work with time trackers over HTTP API, so in case of
any questions, please refer to their official documentation in the first place:

- [Project Laboratory][pl_api_docs]
- [Toggl API Documentation][toggl_api_docs]

[cx_Freeze]: https://anthony-tuininga.github.io/cx_Freeze/
[PyInstaller]: https://www.pyinstaller.org/
[pl]: https://pl.itcraft.co/
[pl_api_docs]: https://pl.itcraft.co/api/docs
[toggl]: https://toggl.com
[toggl_api_docs]: https://github.com/toggl/toggl_api_docs
