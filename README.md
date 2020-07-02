
# BlueCat Ansible Tests and Examples

## Original bluecat.py

requires a change in the bluecat.py to allow parsing the json data returned (original code returns byte)

the code is not idempotent, because it asks for a given action (get, getall, post, patch, delete) and will return an error, if a object already exists.

```bash
ANSIBLE_CONFIG=ansible.cfg ansible-playbook play-bluecat.yml --limit="api.bluecat.metro-cc.com"
```


## Sample Module (DNSzone)

This Module was created to figure out if the bluecat.py & BlueCat Gateway can be used in a more Ansible like way.
Unfortunally the bluecat.py has no setup.py, so it had to be "installed" manually.

e.g.: in a virtualenv /venvbc/
```bash
mkdir /venvbc/lib/python3.6/site-packages/bluecat
cp bluecat.py /venvbc/lib/python3.6/site-packages/bluecat
touch /venvbc/lib/python3.6/site-packages/bluecat/__init__.py
```

Running the Module

```bash
ANSIBLE_CONFIG=ansible.cfg ansible-playbook play-bluecat_dnszone.yml --limit="api.bluecat.metro-cc.com"
```

Gives this Output (with inventories/group_vars/all.yml -> debug_bc: true)
!!Return keys/values in error cases are not yet properly filled!!

```python
PLAY [Test BC GW API via Ansible] ****************************************************************************************************************************************

TASK [present DNS Zone] **************************************************************************************************************************************************
changed: [api.bluecat.metro-cc.com]

TASK [debug present Zone] ************************************************************************************************************************************************
ok: [api.bluecat.metro-cc.com] => {
    "result": {
        "changed": true,
        "configuration": "DE-MCC",
        "deployable": true,
        "failed": false,
        "full_zone": "bluecat4.metro-cc.com",
        "id": 101405,
        "msg": "",
        "original_message": {
            "id": 101405,
            "name": "bluecat4",
            "properties": "deployable=true|absoluteName=bluecat4.metro-cc.com|",
            "type": "Zone"
        },
        "status": 201,
        "view": "internal"
    }
}

TASK [Unchanged present DNS Zone] ****************************************************************************************************************************************
ok: [api.bluecat.metro-cc.com]

TASK [debug unchanged Zone] **********************************************************************************************************************************************
ok: [api.bluecat.metro-cc.com] => {
    "result": {
        "changed": false,
        "configuration": "DE-MCC",
        "deployable": true,
        "failed": false,
        "full_zone": "bluecat4.metro-cc.com",
        "id": 101405,
        "msg": "",
        "original_message": {
            "id": 101405,
            "name": "bluecat4",
            "properties": "deployable=true|absoluteName=bluecat4.metro-cc.com|",
            "type": "Zone"
        },
        "status": 200,
        "view": "internal"
    }
}

TASK [Absent DNS Zone] ***************************************************************************************************************************************************
changed: [api.bluecat.metro-cc.com]

TASK [debug Absent Zone] *************************************************************************************************************************************************
ok: [api.bluecat.metro-cc.com] => {
    "result": {
        "changed": true,
        "configuration": "DE-MCC",
        "failed": false,
        "msg": "",
        "original_message": {
            "msg": "Object Deleted"
        },
        "status": 204,
        "view": "internal"
    }
}

TASK [Unchanged Absent DNS Zone] *****************************************************************************************************************************************
ok: [api.bluecat.metro-cc.com]

TASK [debug unchanged Absent Zone] ***************************************************************************************************************************************
ok: [api.bluecat.metro-cc.com] => {
    "result": {
        "changed": false,
        "failed": false,
        "msg": "Bad Status Code",
        "original_message": "No matching Zone(s) found",
        "status": 404
    }
}

PLAY RECAP ***************************************************************************************************************************************************************
api.bluecat.metro-cc.com   : ok=8    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```