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
  pyenv_root:
    description:
    - PYENV_ROOT
    required: false
    type: str
    default: null
  skip_existing:
    description:
    - the "-s/--skip-existing" option of pyenv install
    required: false
    type: bool
    default: true
  subcommand:
    description:
    - pyenv subcommand
    choices: ["install", "uninstall", "versions", "global"]
    required: false
    default: install
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
    var: result["versions"]

- name: pyenv install -l
  pyenv:
    list: yes
    pyenv_root: "{{ansible_env.HOME}}/.pyenv"
  register: result
- debug:
    var: result["versions"]

- name: pyenv versions --bare
  pyenv:
    subcommand: versions
    pyenv_root: "{{ansible_env.HOME}}/.pyenv"
  register: result
- debug:
    var: result["versions"]
'''

RETURNS = '''
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


def get_versions(module, cmd_path, **kwargs):
    rc, out, err = module.run_command(
        [cmd_path, "versions", "--bare"], **kwargs)
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
    result, data = get_versions(module, cmd_path, **kwargs)
    if not result:
        module.fail_json(**data)
        return None
    if version not in data["versions"]:
        module.exit_json(changed=False, failed=False, stdout="", stderr="")
        return None
    cmd = [cmd_path, "uninstall", "-f", version]
    rc, out, err = module.run_command(cmd, **kwargs)
    if rc:
        module.fail_json(msg=err, stdout=out)
    else:
        module.exit_json(changed=True, failed=False, stdout=out, stderr=err)


def get_global(module, cmd_path, **kwargs):
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
    result, data = get_global(module, cmd_path, **kwargs)
    if not result:
        module.fail_json(**data)
        return None
    if set(data["versions"]) == set(versions):
        module.exit_json(
            changed=False, failed=False, stdout="", stderr="",
            versions=versions)
        return None
    rc, out, err = module.run_command(
        [cmd_path, "global"] + versions, **kwargs)
    if rc:
        module.fail_json(msg=err, stdout=out)
    else:
        module.exit_json(
            changed=True, failed=False, stdout=out, stderr=err,
            versions=versions)


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
        "version": {"required": False, "type": "str", "default": None},
        "versions": {"required": False, "type": "list", "default": None},
        "pyenv_root": {"required": False, "default": None},
        "subcommand": {
            "required": False, "default": "install",
            "choices": ["install", "uninstall", "versions", "global"]
        },
        "force": {"required": False, "type": "bool", "default": None},
        "skip_existing": {"required": False, "type": "bool", "default": None},
        "expanduser": {"required": False, "type": "bool", "default": True},
        "list": {"required": False, "type": "bool", "default": False},
    })
    params = module.params
    environ_update = {}
    pyenv_root = get_pyenv_root(params)
    if pyenv_root is None:
        return module.fail_json(
            msg=MSGS["required_pyenv_root"])
    environ_update["PYENV_ROOT"] = pyenv_root
    cmd_path = os.path.join(pyenv_root, "bin", "pyenv")

    cmd = [cmd_path, params["subcommand"]]
    if params["subcommand"] == "install":
        if params["list"]:
            cmd_install_list(
                module, cmd_path, environ_update=environ_update)
            return None
        if params["skip_existing"] is None:
            if params["force"] is None:
                force = False
                cmd.append("-s")
            elif params["force"] is True:
                force = True
                cmd.append("-f")
            else:
                force = False
                cmd.append("-s")
        else:
            if params["skip_existing"] is True:
                force = False
                cmd.append("-s")
            else:
                # skip_existing: False
                if params["force"] is True:
                    force = True
                    cmd.append("-f")
                else:
                    force = False
    elif params["subcommand"] == "uninstall":
        if not params["version"]:
            module.fail_json(
                msg="uninstall subcommand requires the 'version' parameter")
            return None
        cmd_uninstall(
            module, cmd_path, params["version"], environ_update=environ_update)
        return None
    elif params["subcommand"] == "versions":
        # get_install_list(module, cmd_path)
        cmd_versions(module, cmd_path, environ_update=environ_update)
        return None
    elif params["subcommand"] == "global":
        if params["versions"]:
            cmd_set_global(
                module, cmd_path, params["versions"],
                environ_update=environ_update)
        else:
            cmd_get_global(module, cmd_path, environ_update=environ_update)
        return None
    cmd.append(params["version"])

    rc, out, err = module.run_command(cmd, environ_update=environ_update)
    if rc:
        module.fail_json(msg=err, stdout=out)
    else:
        if force:
            changed = True
        else:
            if out:
                changed = True
            else:
                changed = False
        module.exit_json(changed=changed, failed=False, stdout=out, stderr=err)


if __name__ == '__main__':
    main()
