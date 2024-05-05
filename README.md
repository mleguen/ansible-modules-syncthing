# Ansible Modules for Syncthing

Forked from [github.com/rafi/ansible-modules-syncthing]
(https://github.com/rafi/ansible-modules-syncthing).

Collection of modules for [Syncthing](https://syncthing.net) management.

## Install

Copy the `./library` & `module_utils` directories to your Ansible project and ensure your
`ansible.cfg` has these lines:

```ini
[defaults]
library = ./library
module_utils = ./module_utils
```

Please note this module was tested on:

* Debian Buster with Syncthing v1.0.0

Please report successful usage on other platforms/versions.

## Usage

See [example playbooks](./playbooks) for robust feature usage:

* [install_syncthing.yml] - Install Syncthing on Debian/Ubuntu (with systemd)
* [manage.yml] - Ensure Syncthing devices and folders across devices

## Modules

### Module: `syncthing_facts`

Gather Syncthing facts into `ansible_facts.syncthing`:

- `api_key`: API key (auto-detected if not provided)
- `config`: config read from the API
- `host`: API host (auto-detected if not provided)
- `id`: device ID
- `validate_certs`: should we validate the API TLS certificate?

The auto-detection requires the module to be read with a user with read access on the Syncthing config file.

Examples:

```yml
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
```

### Module: `syncthing_device`

Manage synced devices. Add, remove or pause devices using ID.

Examples:

```yml
# Add a device to share with, use auto-configuration
- name: Add syncthing device
  syncthing_device:
    id: ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG
    name: my-device-name

- name: Gather syncthing facts
  syncthing_facts:

# Add a device to share with, use gathered facts
- name: Add syncthing device
  syncthing_device:
    id: ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG
    name: my-other-device
    host: "{{ syncthing.host }}"
    api_key: "{{ syncthing.api_key }}"
    validate_certs: "{{ syncthing.validate_certs | bool }}"

# Pause an existing device
- name: Pause syncthing device
  syncthing_device:
    id: ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG
    name: my-device-name
    state: pause

# Remove an existing device
- name: Remove syncthing device
  syncthing_device:
    id: ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG
    name: my-device-name
    state: absent
```

### Module: `syncthing_folder`

Manage synced devices. Add, remove or pause devices using ID.

Examples:

```yml
# Add a folder to synchronize with another device, use auto-configuration
- name: Add syncthing folder
  syncthing_folder:
    path: ~/Documents
    id: documents
    devices:
      - ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG

- name: Gather syncthing facts
  syncthing_facts:

# Add a folder to share with several devices, use gathered facts
- name: Add syncthing folder
  syncthing_folder:
    path: ~/Downloads
    id: downloads
    devices:
      - ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG
      - GFEDCBA-GFEDCBA-GFEDCBA-GFEDCBA-GFEDCBA-GFEDCBA-GFEDCBA-GFEDCBA
    host: "{{ syncthing.host }}"
    api_key: "{{ syncthing.api_key }}"
    validate_certs: "{{ syncthing.validate_certs | bool }}"

# Pause an existing folder
- name: Pause syncthing folder
  syncthing_folder:
    id: downloads
    state: pause

# Remove an existing folder
- name: Remove syncthing folder
  syncthing_folder:
    id: downloads
    state: absent
```

## License

Copyright: (c) 2018, Rafael Bodill `<justrafi at g>`
Copyright: (c) 2020--2021, Borjan Tchakaloff `<first name at last name dot fr>`
GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
