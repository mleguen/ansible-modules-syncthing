# Ansible Modules for Syncthing

Forked from [github.com/rafi/ansible-modules-syncthing]
(https://github.com/rafi/ansible-modules-syncthing).

Collection of modules for [Syncthing](https://syncthing.net) management.

## Install

Copy the `./library` directory to your Ansible project and ensure your
`ansible.cfg` has this line:

```ini
[defaults]
library = ./library
```

Alternatively, you can clone this repo locally, and symlink the contents of the `library` folder somewhere in your [default module path](https://docs.ansible.com/ansible/latest/reference_appendices/config.html#default-module-path), eg:

```bash
cd ${ANSIBLE_HOME:-~/.ansible}
mkdir -p plugins/modules
cd plugins/modules
ln -s /path/to/your/local/clone/of/ansible-modules-syncthing/library/* .
```

Please note this module was tested on:

* Debian Buster with Syncthing v1.0.0

Please report successful usage on other platforms/versions.

## Usage

See [example playbooks](./playbooks) for robust feature usage:

* [install_syncthing.yml] - Install Syncthing on Debian/Ubuntu (with systemd)
* [manage.yml] - Ensure Syncthing devices and folders across devices

## Modules

### Module: `syncthing_device`

Manage synced devices. Add, remove or pause devices using ID.

Examples:

```yml
# Add a device to share with, use auto-configuration
- name: Add syncthing device
  syncthing_device:
    id: ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG
    name: my-device-name

# Add a device to share with
- name: Add syncthing device
  syncthing_device:
    id: ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG
    name: my-other-device
    host: http://127.0.0.1:8384
    api_key: aBCDeFG1h2IJKlmNopq3rs45uvwxy6Zz

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

# Add a folder to share with several devices, specify host and api key
- name: Add syncthing folder
  syncthing_folder:
    path: ~/Downloads
    id: downloads
    devices:
      - ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG-ABCDEFG
      - GFEDCBA-GFEDCBA-GFEDCBA-GFEDCBA-GFEDCBA-GFEDCBA-GFEDCBA-GFEDCBA
    host: http://127.0.0.1:8384
    api_key: aBCDeFG1h2IJKlmNopq3rs45uvwxy6Zz

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
