# ansible-pyenv-module

[![Build Status](https://travis-ci.org/suzuki-shunsuke/ansible-pyenv-module.svg?branch=master)](https://travis-ci.org/suzuki-shunsuke/ansible-pyenv-module)

ansible module to run pyenv command.

https://galaxy.ansible.com/suzuki-shunsuke/pyenv-module/

## Notice

* This module doesn't support the [check mode](http://docs.ansible.com/ansible/dev_guide/developing_modules_general.html#supporting-check-mode)

## Supported platform

* GenericLinux
* MacOSX

We test this module in

* Ubuntu 16.04 (Vagrant, Virtualbox)
* CentOS 7.3 (Vagrant, Virtualbox)
* MaxOS Sierra 10.12.5

## Requirements

* [pyenv](https://github.com/pyenv/pyenv)
* [python build dependencies](https://github.com/pyenv/pyenv/wiki/Common-build-problems#requirements)
* [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv): required if you want to run `virtualenv` or `virtualenvs` subcommand

If you want to install pyenv and python build dependencies with ansible role, we recommend the [suzuki-shunsuke.pyenv](https://galaxy.ansible.com/suzuki-shunsuke/pyenv/).
And if you want to install pyenv-virtualenv with ansible role, we recommend the [suzuki-shunsuke.pyenv-virtualenv](https://galaxy.ansible.com/suzuki-shunsuke/pyenv-virtualenv/).

## Supported pyenv subcommands and options

```
$ pyenv install [-s] [-f] <version>
$ pyenv uninstall -f <version>
$ pyenv install -l
$ pyenv versions [--bare]
$ pyenv global
$ pyenv global <versions>
$ pyenv virtualenv [-f] [--no-pip] [--no-setuptools] [--no-wheel] [--symlinks] [--copies] [--clear] [--without-pip] [version] <virtualenv-name>
$ pyenv virtualenvs [--bare] [--skip-aliases]
```

## Install

```
$ ansible-galaxy install suzuki-shunsuke.pyenv-module
```

```yaml
# playbook.yml

- hosts: default
  roles:
  # After you call this role, you can use this module.
  - suzuki-shunsuke.pyenv-module
```

## Options

In addition to this document, please see [pyenv command reference](https://github.com/pyenv/pyenv/blob/master/COMMANDS.md) and the output of `pyenv help <command>` command also.

### Common Options

name | type | required | default | choices / example | description
--- | --- | --- | --- | --- | ---
subcommand | str | no | install | [install, uninstall, versions, global, virtualenvs, virtualenv] |
pyenv_root | str | no | | ~/.pyenv | If the environment variable "PYENV_ROOT" is not set, this option is required
expanduser | bool | no | yes | | By default the environment variable PYENV_ROOT and "pyenv_root" option are filtered by [os.path.expanduser](https://docs.python.org/2.7/library/os.path.html#os.path.expanduser)

### Options of the "install" subcommand

parameter | type | required | default | choices / example | description
--- | --- | --- | --- | --- | ---
version | str | no | | 3.6.1 |
list | bool | no | no | | -l option
skip_existing | bool | no | yes | | -s option
force | bool | no | no | | -f option

Either "version" or "list" option is required.
If the "list" option is set, the return value of that task has "versions" field.

### Options of the "uninstall" subcommand

parameter | type | required | default | choices / example | description
--- | --- | --- | --- | --- | ---
version | str | yes | | 2.7.13 |

### Options of the "global" subcommand

parameter | type | required | default | choices | description
--- | --- | --- | --- | --- | ---
versions | list | no | | |

The return value of the "global" subcommand has "versions" field.

### Options of the "versions" subcommand

parameter | type | required | default | choices | description
--- | --- | --- | --- | --- | ---
bare | bool | no | yes | |

The return value of the "versions" subcommand has "versions" field.

### Options of the "virtualenvs" subcommand

parameter | type | required | default | choices | description
--- | --- | --- | --- | --- | ---
skip_aliases | bool | no | yes | |
bare | bool | no | yes | |

The return value of the "virtualenvs" subcommand has "virtualenvs" field.

### Options of the "virtualenv" subcommand

https://github.com/pyenv/pyenv-virtualenv#virtualenv-and-venv

> `pyenv-virtualenv` uses `python -m venv` if it is available and the `virtualenv` command is not available.

options of the "virtualenv" subcommand depend on whether `pyenv-virtualenv` uses `python -m venv` or not.

#### Common options

parameter | type | required | default | example | description
--- | --- | --- | --- | --- | ---
force | bool | no | no | |
version | str | yes | | 2.7.13 |
virtualenv_name | str | yes | | ansible |

> ##### Notice: force option doesn't work as expected
> This is pyenv-virtualenv's problem. 
>
> https://github.com/pyenv/pyenv-virtualenv/issues/161

#### `virtualenv` options

parameter | type | required | default | example | description
--- | --- | --- | --- | --- | ---
always_copy | bool | no | no | |
no_pip | bool | no | no | |
no_setuptools | bool | no | no | |
no_wheel | bool | no | no | |

See [the virtualenv official documentation](https://virtualenv.pypa.io/en/stable/reference/#virtualenv-command) and the output of the `virtualenv --help` command.

#### `python -m venv` options

parameter | type | required | default | example | description
--- | --- | --- | --- | --- | ---
clear | bool | no | no | |
copies | bool | no | no | |
symlinks | bool | no | no | |
without_pip | bool | no | no | |

See [the venv official documentation](https://docs.python.org/3/library/venv.html) and the output of the `python -m venv -h` command.

> ##### Notice: clear option doesn't work as expected
> This is pyenv-virtualenv's problem. 

## Example

```yaml
- name: pyenv install -s 3.6.1
  pyenv:
    version: 3.6.1
    pyenv_root: "~/.pyenv"

- name: pyenv install -f 3.6.1
  pyenv:
    version: 3.6.1
    pyenv_root: "~/.pyenv"
    force: yes

- name: pyenv uninstall -f 2.6.9
  pyenv:
    subcommand: uninstall
    version: 2.6.9
    pyenv_root: "~/.pyenv"

- name: pyenv global 3.6.1
  pyenv:
    subcommand: global
    versions:
    - 3.6.1
    pyenv_root: "~/.pyenv"

- name: pyenv global
  pyenv:
    subcommand: global
    pyenv_root: "~/.pyenv"
  register: result
- debug:
    var: result.versions

- name: pyenv install -l
  pyenv:
    list: yes
    pyenv_root: "{{ansible_env.HOME}}/.pyenv"
  register: result
- debug:
    var: result.versions

- name: pyenv versions --bare
  pyenv:
    subcommand: versions
    pyenv_root: "{{ansible_env.HOME}}/.pyenv"
  register: result
- debug:
    var: result.versions

- name: pyenv virtualenvs --skip-aliases --bare
  pyenv:
    subcommand: virtualenvs
    pyenv_root: "~/.pyenv"
  register: result
- debug:
    var: result.virtualenvs

- name: pyenv virtualenv --force 2.7.13 ansible
  pyenv:
    subcommand: virtualenv
    pyenv_root: "~/.pyenv"
    version: 2.7.13
    virtualenv_name: ansible
    force: yes
```

## Tips

### Install python packages with pip

Now this module doesn't support `pip` subcommand,
but you can do it with [the official pip module](http://docs.ansible.com/ansible/pip_module.html).

```yaml
# install python and create virtualenv before using pip module
- name: pyenv install -s 2.7.13
  pyenv:
    pyenv_root: "{{pyenv_root}}"
    version: 2.7.13
- name: pyenv virtualenv 3.6.1 yaml_env
  pyenv:
    subcommand: virtualenv
    pyenv_root: "{{pyenv_root}}"
    version: 3.6.1
    virtualenv_name: yaml_env

# use pip module with executable option
- name: install ansible
  pip:
    name: ansible
    executable: "{{pyenv_root}}/versions/2.7.13/bin/pip"
- name: install pyyaml on the virtualenv "yaml_env"
  pip:
    name: pyyaml
    executable: "{{pyenv_root}}/versions/yaml_env/bin/pip"
```

## Change Log

See [CHANGELOG.md](CHANGELOG.md).

## Licence

[MIT](LICENSE)

## Develop

### Requirements

* Vagrant
* Ansible
* Node.js
* yarn

### Setup

```
$ yarn install
$ cd tests
$ ansible-galaxy install -r roles.yml
```

### Test

```
$ cd tests
$ vagrant up --provision
```
