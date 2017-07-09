#!/usr/bin/python
# -*- coding: utf-8 -*-

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: pyenv
short_description: Run pyenv command
options:
  always_copy:
    description:
    - the "--always-copy" option of pyenv virtualenv
    required: false
    type: bool
    default: false
  bare:
    description:
    - the "--bare" option of "versions" and "virtualenvs" subcommand
    required: false
    type: bool
    default: true
  clear:
    description:
    - the "--clear" option of pyenv virtualenv
    required: false
    type: bool
    default: false
  copies:
    description:
    - the "--copies" option of pyenv virtualenv
    required: false
    type: bool
    default: false
  expanduser:
    description:
    - whether the environment variable PYENV_ROOT and "pyenv_root" option are filtered by os.path.expanduser
    required: false
    type: bool
    default: true
  force:
    description:
    - the "-f/--force" option of pyenv install
    required: false
    type: bool
    default: false
  list:
    description:
    - -l/--list option of pyenv install command
    required: false
    type: bool
    default: false
  no_pip:
    description:
    - the "--no-pip" option of pyenv virtualenv
    required: false
    type: bool
    default: false
  no_setuptools:
    description:
    - the "--no-setuptools" option of pyenv virtualenv
    required: false
    type: bool
    default: false
  no_wheel:
    description:
    - the "--no-wheel" option of pyenv virtualenv
    required: false
    type: bool
    default: false
  pyenv_root:
    description:
    - PYENV_ROOT
    required: false
    type: str
    default: null
  skip_aliases:
    description:
    - the "-s/--skip-aliases" option of pyenv virtualenvs
    required: false
    type: bool
    default: true
  skip_existing:
    description:
    - the "-s/--skip-existing" option of pyenv install
    required: false
    type: bool
    default: true
  subcommand:
    description:
    - pyenv subcommand
    choices: ["install", "uninstall", "versions", "global", "virtualenv", "virtualenvs"]
    required: false
    default: install
  symlinks:
    description:
    - the "--symlinks" option of pyenv virtualenv
    required: false
    type: bool
    default: false
  version:
    description:
    - A python version name
    type: str
    required: false
    default: null
  versions:
    description:
    - python version names
    type: list
    required: false
    default: null
  virtualenv_name:
    description:
    - A virtualenv name
    type: str
    required: false
    default: null
  without_pip:
    description:
    - the "--without_pip" option of pyenv virtualenv
    required: false
    type: bool
    default: false
requirements:
- pyenv
author: "Suzuki Shunsuke"
'''

EXAMPLES = '''
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
    pyenv_root: "~/.pyenv"
  register: result
- debug:
    var: result.versions

- name: pyenv versions --bare
  pyenv:
    subcommand: versions
    pyenv_root: "~/.pyenv"
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
'''

RETURNS = '''
virtualenvs:
  description: the return value of `pyenv virtualenvs`
  returned: success
  type: list
  sample:
  - 3.6.1/envs/neovim
  - neovim
versions:
  description: the return value of `pyenv install --list` or `pyenv global` or `pyenv versions`
  returned: success
  type: list
  sample:
  - 2.7.13
  - 3.6.1
'''

import os  # noqa E402

from ansible.module_utils.basic import AnsibleModule  # noqa E402


def wrap_get_func(func):
    def wrap(module, *args, **kwargs):
        result, data = func(module, *args, **kwargs)
        if result:
            module.exit_json(**data)
        else:
            module.fail_json(**data)

    return wrap


def get_install_list(module, cmd_path, **kwargs):
    """ pyenv install --list
    """
    rc, out, err = module.run_command([cmd_path, "install", "-l"], **kwargs)
    if rc:
        return (False, dict(msg=err, stdout=out))
    else:
        # slice: remove header and last newline
        versions = [line.strip() for line in out.split("\n")[1:-1]]
        return (True, dict(
            changed=False, failed=False, stdout=out, stderr=err,
            versions=versions))


cmd_install_list = wrap_get_func(get_install_list)


def get_versions(module, cmd_path, bare, **kwargs):
    """ pyenv versions [--bare]
    """
    cmd = [cmd_path, "versions"]
    if bare:
        cmd.append("--bare")
    rc, out, err = module.run_command(cmd, **kwargs)
    if rc:
        return (False, dict(msg=err, stdout=out))
    else:
        # slice: remove last newline
        versions = [line.strip() for line in out.split("\n")[:-1]]
        return (True, dict(
            changed=False, failed=False, stdout=out, stderr=err,
            versions=versions))


cmd_versions = wrap_get_func(get_versions)


def cmd_uninstall(module, cmd_path, version, **kwargs):
    """ pyenv uninstall --force <version>
    """
    result, data = get_versions(module, cmd_path, True, **kwargs)
    if not result:
        return module.fail_json(**data)
    if version not in data["versions"]:
        return module.exit_json(
            changed=False, failed=False, stdout="", stderr="")
    cmd = [cmd_path, "uninstall", "-f", version]
    rc, out, err = module.run_command(cmd, **kwargs)
    if rc:
        module.fail_json(msg=err, stdout=out)
    else:
        module.exit_json(changed=True, failed=False, stdout=out, stderr=err)


def get_global(module, cmd_path, **kwargs):
    """ pyenv global
    """
    rc, out, err = module.run_command([cmd_path, "global"], **kwargs)
    if rc:
        return (False, dict(msg=err, stdout=out))
    else:
        # slice: remove last newline
        versions = [line.strip() for line in out.split("\n")[:-1]]
        return (True, dict(
            changed=False, failed=False, stdout=out, stderr=err,
            versions=versions))


cmd_get_global = wrap_get_func(get_global)


def cmd_set_global(module, cmd_path, versions, **kwargs):
    """ pyenv global <version> [<version> ...]
    """
    result, data = get_global(module, cmd_path, **kwargs)
    if not result:
        return module.fail_json(**data)
    if set(data["versions"]) == set(versions):
        return module.exit_json(
            changed=False, failed=False, stdout="", stderr="",
            versions=versions)
    rc, out, err = module.run_command(
        [cmd_path, "global"] + versions, **kwargs)
    if rc:
        module.fail_json(msg=err, stdout=out)
    else:
        module.exit_json(
            changed=True, failed=False, stdout=out, stderr=err,
            versions=versions)


def cmd_install(module, params, cmd_path, **kwargs):
    """ pyenv install [--skip-existing] [--force] <version>
    """
    cmd = [cmd_path, "install"]
    if params["skip_existing"] is not False:
        force = False
        cmd.append("--skip-existing")
    elif params["force"] is True:
        force = True
        cmd.append("--force")

    cmd.append(params["version"])

    rc, out, err = module.run_command(cmd, **kwargs)
    if rc:
        return module.fail_json(msg=err, stdout=out)
    else:
        changed = force or out
        return module.exit_json(
            changed=changed, failed=False, stdout=out, stderr=err)


def get_virtualenvs(module, cmd_path, skip_aliases, bare, **kwargs):
    """ pyenv virtualenvs [--skip-aliases] [--bare]
    """
    cmd = [cmd_path, "virtualenvs"]
    if skip_aliases:
        cmd.append("--skip-aliases")
    if bare:
        cmd.append("--bare")
    rc, out, err = module.run_command(cmd, **kwargs)
    if rc:
        return (False, dict(msg=err, stdout=out))
    else:
        # slice: remove last newline
        virtualenvs = [line.strip() for line in out.split("\n")[:-1]]
        return (True, dict(
            changed=False, failed=False, stdout=out, stderr=err,
            virtualenvs=virtualenvs))


cmd_virtualenvs = wrap_get_func(get_virtualenvs)


def cmd_virtualenv(
        module, cmd_path, version, virtualenv_name, options, **kwargs):
    """ pyenv virtualenv [--force] <version> <virtualenv name>
    """
    cmd = [cmd_path, "virtualenv"]
    
    for key in [
            "force", "no_pip", "no_setuptools", "no_wheel", "symlinks",
            "copies", "clear", "without_pip"]:
        if options[key]:
            cmd.append("--{}".format(key.replace("_", "-")))
    if options["force"]:
        # pyenv virtualenv --force not working as expected?
        # https://github.com/pyenv/pyenv-virtualenv/issues/161
        cmd.append("--force")
        cmd.append(version)
        cmd.append(virtualenv_name)
        rc, out, err = module.run_command(cmd, **kwargs)
        if rc:
            return module.fail_json(msg=err, stdout=out)
        else:
            return module.exit_json(
                changed=True, failed=False, stdout=out, stderr=err)
    if options["clear"]:
        # pyenv virtualenv --clear not working as expected?
        cmd.append(version)
        cmd.append(virtualenv_name)
        rc, out, err = module.run_command(cmd, **kwargs)
        if rc:
            return module.fail_json(msg=err, stdout=out)
        else:
            return module.exit_json(
                changed=True, failed=False, stdout=out, stderr=err)

    result, data = get_virtualenvs(module, cmd_path, False, True, **kwargs)
    if not result:
        return module.fail_json(**data)
    virtualenvs = set(data["virtualenvs"])
    if virtualenv_name in virtualenvs:
        if "{}/envs/{}".format(version, virtualenv_name) in virtualenvs:
            return module.exit_json(
                changed=False, failed=False,
                stdout="{} already exists".format(virtualenv_name), stderr="")
        else:
            return module.fail_json(
                msg="{} already exists but version differs".format(
                    virtualenv_name))

    cmd.append(version)
    cmd.append(virtualenv_name)

    rc, out, err = module.run_command(cmd, **kwargs)
    if rc:
        return module.fail_json(msg=err, stdout=out)
    else:
        return module.exit_json(
            changed=True, failed=False, stdout=out, stderr=err)


MSGS = {
    "required_pyenv_root": (
        "Either the environment variable 'PYENV_ROOT' "
        "or 'pyenv_root' option is required")
}


def get_pyenv_root(params):
    if params["pyenv_root"]:
        if params["expanduser"]:
            return os.path.expanduser(params["pyenv_root"])
        else:
            return params["pyenv_root"]
    else:
        if "PYENV_ROOT" not in os.environ:
            return None
        if params["expanduser"]:
            return os.path.expanduser(os.environ["PYENV_ROOT"])
        else:
            return os.environ["PYENV_ROOT"]


def main():
    module = AnsibleModule(argument_spec={
        "bare": {"required": False, "type": "bool", "default": True},
        "copies": {"required": False, "type": "bool", "default": False},
        "clear": {"required": False, "type": "bool", "default": False},
        "force": {"required": False, "type": "bool", "default": None},
        "expanduser": {"required": False, "type": "bool", "default": True},
        "list": {"required": False, "type": "bool", "default": False},
        "no_pip": {"required": False, "type": "bool", "default": False},
        "no_setuptools": {"required": False, "type": "bool", "default": False},
        "no_wheel": {"required": False, "type": "bool", "default": False},
        "pyenv_root": {"required": False, "default": None},
        "skip_aliases": {"required": False, "type": "bool", "default": True},
        "skip_existing": {"required": False, "type": "bool", "default": None},
        "subcommand": {
            "required": False, "default": "install",
            "choices": [
                "install", "uninstall", "versions", "global",
                "virtualenv", "virtualenvs"]
        },
        "symlinks": {"required": False, "type": "bool", "default": False},
        "version": {"required": False, "type": "str", "default": None},
        "versions": {"required": False, "type": "list", "default": None},
        "virtualenv_name": {"required": False, "type": "str", "default": None},
        "without_pip": {"required": False, "type": "bool", "default": False},
    })
    params = module.params
    environ_update = {}
    pyenv_root = get_pyenv_root(params)
    if pyenv_root is None:
        return module.fail_json(
            msg=MSGS["required_pyenv_root"])
    environ_update["PYENV_ROOT"] = pyenv_root
    cmd_path = os.path.join(pyenv_root, "bin", "pyenv")

    if params["subcommand"] == "install":
        if params["list"]:
            return cmd_install_list(
                module, cmd_path, environ_update=environ_update)
        return cmd_install(
            module, params, cmd_path, environ_update=environ_update)
    elif params["subcommand"] == "uninstall":
        if not params["version"]:
            return module.fail_json(
                msg="uninstall subcommand requires the 'version' parameter")
        return cmd_uninstall(
            module, cmd_path, params["version"], environ_update=environ_update)
    elif params["subcommand"] == "versions":
        return cmd_versions(
            module, cmd_path, params["bare"], environ_update=environ_update)
    elif params["subcommand"] == "global":
        if params["versions"]:
            return cmd_set_global(
                module, cmd_path, params["versions"],
                environ_update=environ_update)
        else:
            return cmd_get_global(
                module, cmd_path, environ_update=environ_update)
    elif params["subcommand"] == "virtualenvs":
        return cmd_virtualenvs(
            module, cmd_path, params["skip_aliases"], params["bare"],
            environ_update=environ_update)
    elif params["subcommand"] == "virtualenv":
        if not params["version"]:
            return module.fail_json(
                msg="virtualenv subcommand requires the 'version' parameter")
        if not params["virtualenv_name"]:
            return module.fail_json(
                msg=(
                    "virtualenv subcommand requires the 'virtualenv_name' "
                    "parameter"))
        options = dict((key, params[key]) for key in [
            "force", "no_pip", "no_setuptools", "no_wheel", "symlinks",
            "copies", "clear", "without_pip"])
        return cmd_virtualenv(
            module, cmd_path, params["version"], params["virtualenv_name"],
            options, environ_update=environ_update)


if __name__ == '__main__':
    main()
