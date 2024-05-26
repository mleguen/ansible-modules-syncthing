#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Rafael Bodill <justrafi at google mail>
# Copyright: (c) 2020, Borjan Tchakaloff <first name at last name dot fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
module: syncthing_gui

short_description: Configure Syncthing GUI

version_added: "2.8"

description: Configure Syncthing GUI via the REST API

options:
    host:
        description:
            - Host to connect to, including protocole & port.
              If not provided, will try to auto-configure from filesystem.
        required: false
    validate_certs:
        description:
            - Should calls to host fail when the certificate is invalid?
        default: true
    api_key:
        description:
            - API key to use for authentication with host.
              If not provided, will try to auto-configure from filesystem.
        required: false
    config_file:
        description:
            - Path to the Syncthing configuration file for automatic
              discovery (`host` & `api_key`). Note that the running user needs read
              access to the file.
        required: false
    timeout:
        description:
            - The socket level timeout in seconds
        default: 30
    useTLS:
        description:
            - If set to true, TLS (HTTPS) will be enforced.
              Non-HTTPS requests will be redirected to HTTPS.
              When set to false, TLS connections are still possible but not required.
        default: false
    address:
        description:
            - Set the listen address 
        default: 127.0.0.1:8384
    user:
        description:
            - Set to require authentication 
        required: false
    password:
        description:
            - Contains the bcrypt hash of the real password.
              Will be set only when the user changes too
              (as bcrypt hashes cannot be compared)
        required: false

author:
    - Mael Le Guen
'''

EXAMPLES = r'''
- name: Configure GUI
  syncthing_gui:
    host: "{{ syncthing.host }}"
    api_key: "{{ syncthing.api_key }}"
    validate_certs: "{{ syncthing.validate_certs | bool }}"
    useTLS: true
    user: syncthing
    password: "{{ gui_password | password_hash('bcrypt') }}"
'''

RETURN = r'''
ansible_facts:
    description: The gathered facts.
    type: dict
    contains:
        syncthing_config:
            description: the syncthing config read from the REST API
            type: dict
'''

from yaml import safe_dump

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.syncthing import get_common_argument_spec, get_config, post_config


def run_module():
    # module arguments
    module_args = get_common_argument_spec()
    module_args.update(dict(
        useTLS=dict(type='bool', default=False),
        address=dict(type='str', default='127.0.0.1:8384'),
        user=dict(type='str', required=False),
        password=dict(type='str', required=False, no_log=True),
    ))

    # seed the result dict in the object
    result = {
        "changed": False,
        "response": None,
    }

    # the AnsibleModule object will be our abstraction working with Ansible
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    config = get_config(module)[0]
    gui_config = config['gui']
    before = safe_dump(gui_config)

    if gui_config['useTLS'] != module.params['useTLS']:
        gui_config['useTLS'] = module.params['useTLS']
        result['changed'] = True

    if gui_config['address'] != module.params['address']:
        gui_config['address'] = module.params['address']
        result['changed'] = True

    if gui_config['user'] != module.params['user']:
        gui_config['user'] = module.params['user']
        gui_config['password'] = module.params['password']
        result['changed'] = True

    if result['changed']:
        if not module.check_mode:
            post_config(module, config, result)

        result['diff'] = {
            "before": before,
            "after": safe_dump(gui_config), 
        }

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
