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
module: syncthing_facts

short_description: Gather Syncthing facts

version_added: "2.8"

description: Gather syncthing facts from Syncthing's REST API and/or XML config on the filesystem.

options:
    host:
        description:
            - API host to connect to, including protocole & port.
              If not provided, will try to auto-configure from filesystem.
        required: false
    validate_certs:
        description:
            - Whether the API TLS certificate should be validated
              (set to false when using Syncthing's default self-signed
              certificate)
        default: true
    api_key:
        description:
            - API key to use for authentication with host.
              If not provided, will try to auto-configure from filesystem.
        required: false
    config_file:
        description:
            - Path to the Syncthing configuration file for automatic
              discovery (`host` & `api_key`). If not provided, will try to
              auto-detect from standard location. Note that the running user
              needs read access to the file.
        required: false
    timeout:
        description:
            - The socket level timeout in seconds
        default: 30

author:
    - Mael Le Guen
'''

EXAMPLES = r'''
- name: Gather syncthing facts
  syncthing_facts:
    # Mandatory when using Syncthing's default self signed TLS certificate,
    # this choice will be persisted in gathered facts
    validate_certs: false
  become: true
  # Needed only when gathering facts using auto-detection,
  # to ensure read acess to Syncthing's config.xml
  become_user: syncthing

- name: Use gathered facts with other syncthing modules
  syncthing_device:
    host: "{{ syncthing.host }}"
    api_key: "{{ syncthing.api_key }}"
    validate_certs: "{{ syncthing.validate_certs | bool }}"
    # [...]
'''

RETURN = r'''
ansible_facts:
    description: The gathered facts.
    type: dict
    contains:
        syncthing:
            description: Syncthing facts
            type: dict
            contains:
                api_key:
                    description: API key to use for authentication with host
                    type: string
                config:
                    description: The full Syncthing config read from the REST api
                    type: dict
                host:
                    description: API host to connect to, including protocole & port
                    type: string
                id:
                    description: Syncthing device ID of this node
                    type: string
                validate_certs:
                    description: Whether the API TLS certificate should be validated
                    type: bool
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.syncthing import get_common_argument_spec, get_config

def run_module():
    module_args = get_common_argument_spec()
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    config, id = get_config(module)
    result = {
        "changed": False,
        "ansible_facts": {
            "syncthing": {
                "api_key": module.params['api_key'],
                "config": config,
                "host": module.params['host'],
                "id": id,
                "validate_certs": module.params['validate_certs']
            }
        },
    }

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
