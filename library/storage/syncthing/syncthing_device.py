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

DOCUMENTATION = '''
---
module: syncthing_device

short_description: Manage Syncthing devices

version_added: "2.7"

description:
    - "This is my longer description explaining my sample module"

options:
    id:
        description:
            - This is the unique id of this new device
        required: true
    name:
        description:
            - The name for this new device
        required: false
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
    state:
        description:
            - Use present/absent to ensure device is added, or not.
        default: present
        choices: ['absent', 'present', 'paused']

author:
    - Rafael Bodill (@rafi)
'''

EXAMPLES = '''
# Add a device to share with
- name: Add syncthing device
  syncthing_device:
    id: 1234-1234-1234-1234
    name: my-server-name
'''

RETURN = '''
response:
    description: The API response, in-case of an error.
    type: dict
'''

from yaml import safe_dump

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.syncthing import get_common_argument_spec, get_config, post_config


# Returns an object of a new device
def create_device(params):
    device = {
        'addresses': [
            'dynamic'
        ],
        'allowedNetworks': [],
        'autoAcceptFolders': False,
        'certName': '',
        'compression': 'metadata',
        'deviceID': params['id'],
        'ignoredFolders': [],
        'introducedBy': '',
        'introducer': False,
        'maxRecvKbps': 0,
        'maxSendKbps': 0,
        'name': params['name'],
        'paused': True if params['state'] == 'paused' else False,
        'pendingFolders': [],
        'skipIntroductionRemovals': False
    }
    return device

def run_module():
    # module arguments
    module_args = get_common_argument_spec()
    module_args.update(dict(
        id=dict(type='str', required=True),
        name=dict(type='str', required=False),
        state=dict(type='str', default='present',
                   choices=['absent', 'present', 'pause']),
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

    if module.params['state'] != 'absent' and not module.params['name']:
        module.fail_json(msg='You must provide a name when creating', **result)

    config = get_config(module)[0]  
    before = safe_dump(config['devices'])
    if module.params['state'] == 'absent':
        # Remove device from list, if found
        for idx, device in enumerate(config['devices']):
            if device['deviceID'] == module.params['id']:
                config['devices'].pop(idx)
                result['changed'] = True
                break
    else:
        # Bail-out if device is already added
        for device in config['devices']:
            if device['deviceID'] == module.params['id']:
                want_pause = module.params['state'] == 'pause'
                if (want_pause and not device['paused']) or \
                        (not want_pause and device['paused']):
                    device['paused'] = want_pause
                    result['changed'] = True

                break
        # Append the new device into configuration
        else:
            device = create_device(module.params)
            config['devices'].append(device)
            result['changed'] = True

    if result['changed']:
        if not module.check_mode:
            post_config(module, config, result)

        result['diff'] = {
            "before": before,
            "after": safe_dump(config['devices']), 
        }

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
