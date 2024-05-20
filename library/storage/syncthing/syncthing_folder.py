#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Rafael Bodill <justrafi at gmail>
# Copyright: (c) 2020, Borjan Tchakaloff <first name at last name dot fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: syncthing_folder

short_description: Manage Syncthing folders

version_added: "2.7"

description:
    - "This is my longer description explaining my sample module"

options:
    id:
        description:
            - This is the unique id of this new folder
        required: true
    label:
        description:
            - The label for this new folder
        required: false
    path:
        description:
            - This is the path of the folder
        required: false
    devices:
        description:
            - List of devices to share folder with
        required: false
    fs_watcher:
        description:
            - Whether to activate the file-system watcher.
        default: true
    ignore_perms:
        description:
            - Whether to ignore permissions when looking for changes.
        default: false
    type:
        description:
            - The folder type: sending local chances, and/or receiving
              remote changes.
        default: sendreceive
        choices: ['sendreceive', 'sendonly', 'receiveonly']
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
            - Use present/absent to ensure folder is shared, or not.
        default: present
        choices: ['absent', 'present', 'paused']

author:
    - Rafael Bodill (@rafi)
'''

EXAMPLES = '''
# Add a folder to synchronize with another device
- name: Add syncthing folder
  syncthing_folder:
    id: box
    path: ~/box
    devices:
      - 1234-1234-1234-1234
'''

RETURN = '''
response:
    description: The API response, in-case of an error.
    type: dict
'''

from yaml import safe_dump

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.syncthing import get_common_argument_spec, get_config, get_data_from_rest_api, post_config


# Fetch Syncthing status
def get_status(module):
    return get_data_from_rest_api(module, 'system/status')[0]

# Get the device name -> device ID mapping.
def get_devices_mapping(config):
    return {
        device['name']: device['deviceID'] for device in config['devices']
    }

# Get the folder configuration from the global configuration, if it exists
def get_folder_config(folder_id, config):
    for folder in config['folders']:
        if folder['id'] == folder_id:
            return folder
    return None

# Returns an object of a new folder
def create_folder(params, self_id, current_device_ids, devices_mapping):
    # We need the current device ID as per the Syncthing API.
    # If missing, Syncthing will add it alright, but we don't want to give
    # the false idea that this configuration is different just because of that.
    wanted_device_ids = {self_id}
    for device_name_or_id in params['devices']:
        if device_name_or_id in devices_mapping:
            wanted_device_ids.add(devices_mapping[device_name_or_id])
        else:
            # Purposefully do not validate we already know this device ID or
            # name as per previous behavior.  This will need to be fixed.
            wanted_device_ids.add(device_name_or_id)

    # Keep the original ordering if collections are equivalent.
    # Again, for idempotency reasons.
    device_ids = (
        current_device_ids
        if set(current_device_ids) == wanted_device_ids
        else sorted(wanted_device_ids)
    )

    # Sort the device IDs to keep idem-potency
    devices = [
        {
            'deviceID': device_id,
            'encryptionPassword': '',
            'introducedBy': '',
        } for device_id in device_ids
    ]

    return {
        'autoNormalize': True,
        'blockPullOrder': 'standard',
        'caseSensitiveFS': False,
        'copiers': 0,
        'copyOwnershipFromParent': False,
        'copyRangeMethod': 'standard',
        'devices': devices,
        'disableFsync': False,
        'disableSparseFiles': False,
        'disableTempIndexes': False,
        'filesystemType': 'basic',
        'fsWatcherDelayS': 10,
        'fsWatcherEnabled': params['fs_watcher'],
        'hashers': 0,
        'id': params['id'],
        'ignoreDelete': False,
        'ignorePerms': params['ignore_perms'],
        'junctionsAsDirs': False,
        'label': params['label'] if params['label'] else params['id'],
        'markerName': '.stfolder',
        'maxConcurrentWrites': 2,
        'maxConflicts': -1,
        'minDiskFree': {
            'unit': '%',
            'value': 1
        },
        'modTimeWindowS': 0,
        'order': 'random',
        'path': params['path'],
        'paused': True if params['state'] == 'paused' else False,
        'pullerMaxPendingKiB': 0,
        'pullerPauseS': 0,
        'rescanIntervalS': 3600,
        'scanProgressIntervalS': 0,
        'sendOwnership': False,
        'sendXattrs': False,
        'syncOwnership': False,
        'syncXattrs': False,
        'type': params['type'],
        'versioning': {
            'cleanupIntervalS': 3600,
            'fsPath': '',
            'fsType': 'basic',
            'params': {},
            'type': ''
        },
        'weakHashThresholdPct': 25,
        'xattrFilter': {
            'entries': [],
            'maxSingleEntrySize': 1024,
            'maxTotalSize': 4096,
        }
    }

def run_module():
    # module arguments
    module_args = get_common_argument_spec()
    module_args.update(dict(
        id=dict(type='str', required=True),
        label=dict(type='str', required=False),
        path=dict(type='path', required=False),
        devices=dict(type='list', required=False, default=False),
        fs_watcher=dict(type='bool', default=True),
        ignore_perms=dict(type='bool', required=False, default=False),
        type=dict(type='str', default='sendreceive',
            choices=['sendreceive', 'sendonly', 'receiveonly']),
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

    if module.params['state'] != 'absent' and not module.params['path']:
        module.fail_json(msg='You must provide a path when creating', **result)

    config = get_config(module)[0]  
    before = safe_dump(config['folders'])
    self_id = get_status(module)['myID']
    devices_mapping = get_devices_mapping(config)
    if module.params['state'] == 'absent':
        # Remove folder from list, if found
        for idx, folder in enumerate(config['folders']):
            if folder['id'] == module.params['id']:
                config['folders'].pop(idx)
                result['changed'] = True
                break
    else:
        folder_config = get_folder_config(module.params['id'], config)
        folder_config_devices = (
            [d['deviceID'] for d in folder_config['devices']] if folder_config else []
        )
        folder_config_wanted = create_folder(
            module.params, self_id, folder_config_devices, devices_mapping
        )

        if folder_config is None:
            config['folders'].append(folder_config_wanted)
            result['changed'] = True
        elif folder_config != folder_config_wanted:
            # Update the folder configuration in-place
            folder_config.clear()
            folder_config.update(folder_config_wanted)
            result['changed'] = True

    if result['changed']:
        if not module.check_mode:
            post_config(module, config, result)

        result['diff'] = {
            "before": before,
            "after": safe_dump(config['folders']), 
        }

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
