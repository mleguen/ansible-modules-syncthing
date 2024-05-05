#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Rafael Bodill <justrafi at google mail>
# Copyright: (c) 2020, Borjan Tchakaloff <first name at last name dot fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
import json
import platform
from xml.etree.ElementTree import parse

from ansible.module_utils.urls import fetch_url, url_argument_spec

SYNCTHING_API_BASE_URI = "/rest"
if platform.system() == 'Windows':
    DEFAULT_ST_CONFIG_LOCATIONS = ['%localappdata%/Syncthing/config.xml']
elif platform.system() == 'Darwin':
    DEFAULT_ST_CONFIG_LOCATIONS = ['$HOME/Library/Application Support/Syncthing/config.xml']
else:
    DEFAULT_ST_CONFIG_LOCATIONS = [
        '$HOME/.local/state/syncthing/config.xml',
        '$HOME/.config/syncthing/config.xml', # Before syncthing 1.27.0
    ]


def get_common_argument_spec():
    module_args = url_argument_spec()
    module_args.update(dict(
        host=dict(type='str', required=False),
        validate_certs=dict(type='bool', default=True),
        api_key=dict(type='str', required=False, no_log=True),
        config_file=dict(type='str', required=False),
        timeout=dict(type='int', default=30),
    ))
    return module_args

# Fetch Syncthing configuration
def get_config(module):
    return get_data_from_rest_api(module, 'system/config')

def get_data_from_rest_api(module, resource):
    url, headers = make_headers(module, resource)
    resp, info = fetch_url(
        module,
        url,
        data=None,
        headers=headers,
        method='GET',
        timeout=module.params['timeout']
    )

    if not info or info['status'] != 200:
        result = {
            "changed": False,
            "response": info,
        }
        module.fail_json(msg='Error occured while calling host', **result)

    try:
        content = resp.read()
    except AttributeError:
        result = {
            "changed": False,
            "content": info.pop('body', ''),
            "response": str(info),
        }
        module.fail_json(msg='Error occured while reading response', **result)

    return json.loads(content), info.get('x-syncthing-id', None)

def make_headers(module, resource):
    if not module.params['api_key'] or not module.params['host']:
        auto_configuration(module)

    url = '{}{}/{}'.format(module.params['host'], SYNCTHING_API_BASE_URI, resource)
    headers = {'X-Api-Key': module.params['api_key'] }
    return url, headers

def auto_configuration(module):
    if not module.params['config_file']:
        for location in DEFAULT_ST_CONFIG_LOCATIONS:
            path = os.path.expandvars(location)
            if os.path.isfile(path):
                module.params['config_file'] = path
                break
        else:
            module.fail_json(msg="Auto-configuration failed: unable to locate the config file."
                                 " Please specify the host and API key manually.")
    try:
        stconfig = parse(module.params['config_file'])
        root = stconfig.getroot()
        gui = root.find('gui')

        if not module.params['host']:
            tls = gui.attrib.get('tls', 'false') == 'true'
            module.params['host'] = ('https://' if tls else 'http://') + gui.find('address').text

        if not module.params['api_key']:
            module.params['api_key'] = gui.find('apikey').text
    except Exception:
        module.fail_json(msg="Auto-configuration failed: unable to read " + module.params['config_file'] +
                             " Please specify the host and API key manually.")

# Post the new configuration to Syncthing API
def post_config(module, config, result):
    url, headers = make_headers(module, 'system/config')
    headers['Content-Type'] = 'application/json'

    result['msg'] = config
    resp, info = fetch_url(
        module, url, data=json.dumps(config), headers=headers,
        method='POST', timeout=module.params['timeout'])

    if not info or info['status'] != 200:
        result['response'] = str(info)
        module.fail_json(**result)
