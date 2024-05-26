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
            - The folder type: sending local changes, and/or receiving
              remote changes.
        default: sendreceive
        choices: ['sendreceive', 'sendonly', 'receiveonly']
    order:
        description:
            - The order in which needed files should be pulled from the
              cluster. It has no effect when the folder type is “send only”: 
        default: random
        choices: ['random', 'alphabetic', 'smallestFirst', 'largestFirst', 'oldestFirst', 'newestFirst']
    host:
        description:
            - Host to connect to, including port
        default: http://127.0.0.1:8384
    api_key:
        description:
            - API key to use for authentication with host.
              If not provided, will try to auto-configure from filesystem.
        required: false
    config_file:
        description:
            - Path to the Syncthing configuration file for automatic
              discovery (`api_key`). Note that the running user needs read
              access to the file.
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

import os
import json
import platform
from xml.etree.ElementTree import parse

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url, url_argument_spec

SYNCTHING_API_BASE_URI = "/rest"
if platform.system() == 'Windows':
    DEFAULT_ST_CONFIG_LOCATION = '%localappdata%/Syncthing/config.xml'
elif platform.system() == 'Darwin':
    DEFAULT_ST_CONFIG_LOCATION = '$HOME/Library/Application Support/Syncthing/config.xml'
else:
    DEFAULT_ST_CONFIG_LOCATION = '$HOME/.config/syncthing/config.xml'


def make_headers(host, api_key, resource):
    url = '{}{}/{}'.format(host, SYNCTHING_API_BASE_URI, resource)
    headers = {'X-Api-Key': api_key }
    return url, headers

def get_key_from_filesystem(module):
    try:
        if module.params['config_file']:
            stconfigfile = module.params['config_file']
        else:
            stconfigfile = os.path.expandvars(DEFAULT_ST_CONFIG_LOCATION)
        stconfig = parse(stconfigfile)
        root = stconfig.getroot()
        gui = root.find('gui')
        api_key = gui.find('apikey').text
        return api_key
    except Exception:
        module.fail_json(msg="Auto-configuration failed. Please specify"
                             "the API key manually.")

def get_data_from_rest_api(module, resource):
    url, headers = make_headers(
        module.params['host'], module.params['api_key'], resource
    )
    resp, info = fetch_url(
        module,
        url,
        data=None,
        headers=headers,
        method='GET',
        timeout=module.params['timeout']
    )

    if not info or info['status'] != 200:
        result['response'] = info
        module.fail_json(msg='Error occured while calling host', **result)

    try:
        content = resp.read()
    except AttributeError:
        result['content'] = info.pop('body', '')
        result['response'] = str(info)
        module.fail_json(msg='Error occured while reading response', **result)

    return json.loads(content)

# Fetch Syncthing configuration
def get_config(module):
    return get_data_from_rest_api(module, 'system/config')

# Fetch Syncthing status
def get_status(module):
    return get_data_from_rest_api(module, 'system/status')

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

# Post the new configuration to Syncthing API
def post_config(module, config, result):
    url, headers = make_headers(
        module.params['host'],
        module.params['api_key'],
        'system/config',
    )
    headers['Content-Type'] = 'application/json'

    result['msg'] = config
    resp, info = fetch_url(
        module, url, data=json.dumps(config), headers=headers,
        method='POST', timeout=module.params['timeout'])

    if not info or info['status'] != 200:
        result['response'] = str(info)
        module.fail_json(**result)

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
            'introducedBy': '',
        } for device_id in device_ids
    ]

    return {
        'autoNormalize': True,
        'copiers': 0,
        'devices': devices,
        'disableSparseFiles': False,
        'disableTempIndexes': False,
        'filesystemType': 'basic',
        'fsWatcherDelayS': 10,
        'fsWatcherEnabled': params['fs_watcher'],
        'hashers': 0,
        'id': params['id'],
        'ignoreDelete': False,
        'ignorePerms': params['ignore_perms'],
        'label': params['label'] if params['label'] else params['id'],
        'markerName': '.stfolder',
        'maxConflicts': -1,
        'minDiskFree': {
            'unit': '%',
            'value': 1
        },
        'order': params['order'],
        'path': params['path'],
        'paused': True if params['state'] == 'paused' else False,
        'pullerMaxPendingKiB': 0,
        'pullerPauseS': 0,
        'rescanIntervalS': 3600,
        'scanProgressIntervalS': 0,
        'type': params['type'],
        'useLargeBlocks': False,
        'versioning': {
            'params': {},
            'type': ''
        },
        'weakHashThresholdPct': 25
    }

def run_module():
    # module arguments
    module_args = url_argument_spec()
    module_args.update(dict(
        id=dict(type='str', required=True),
        label=dict(type='str', required=False),
        path=dict(type='path', required=False),
        devices=dict(type='list', required=False, default=False),
        fs_watcher=dict(type='bool', default=True),
        ignore_perms=dict(type='bool', required=False, default=False),
        type=dict(type='str', default='sendreceive',
            choices=['sendreceive', 'sendonly', 'receiveonly']),
        order=dict(type='str', default='random',
                   choices=['random', 'alphabetic', 'smallestFirst', 'largestFirst', 'oldestFirst', 'newestFirst']),
        host=dict(type='str', default='http://127.0.0.1:8384'),
        api_key=dict(type='str', required=False, no_log=True),
        config_file=dict(type='path', required=False),
        timeout=dict(type='int', default=30),
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

    if module.check_mode:
        return result

    # Auto-configuration: Try to fetch API key from filesystem
    if not module.params['api_key']:
        module.params['api_key'] = get_key_from_filesystem(module)

    config = get_config(module)
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
        post_config(module, config, result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
