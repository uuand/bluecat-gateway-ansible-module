#!/usr/bin/python

# Copyright: (c) 2020, Jens-Peter Wand <jenswand@googlemail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: bluecat_server

short_description: This module interacts with the BlueCat Gateway rest_api workflow

version_added: "2.x"

description:
    - "Test BlueCat Gateway Zone handling through Ansible"
options:
    fqdn:
        description:
            - This is the FQDN of the Server Object
        required: true
    friendly_name:
        description:
            - This is the Server Name visible in BAM
        required: false
    interface_address:
        description:
            - This is the Server Name visible in BAM
        required: true
    profile:
        description:
            - Server Profile (appliance type) assigned to the server.
        required: false
    configuration:
        description:
            - This is the BlueCat access Manager configuration name the Server resides in
        required: true
    properties section-----------
    deployable:
        description:
            - Should the zone marked as deployable, i.e it will result in a BIND zone declartion (e.g. never set this on a .com zone)
        default: false
        choices:
            - false
            - true
    state:
        description:
            - Wheter the declared state should be present or absent
        default: present
        choices:
            - present
            - absent
    gw_host:
        description:
            - BlueCat Gateway FQDN or IP
        required: true
    gw_username:
        description:
            - BlueCat Gateway User with permissions on rest_api workflow
        required: true
    gw_password:
        description:
            - BlueCat Gateway Password with permissions on rest_api workflow
        required: true
    gw_protocol:
        description:
            - Protocol used to connect to BlueCat Gateway
        default: https
        choices:
            - https
            - http
    gw_apiversion:
        description:
            - BlueCat Gateway api version to use
        default: 1

author:
    - Jens-Peter Wand (@yourhandle)
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  my_test:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_test:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_test:
    name: fail me
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
    returned: always
message:
    description: The output message that the test module generates
    type: str
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule
#import bluecat
from bluecat import bluecat
import os, json

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        resource=dict(type='str', default='servers', choices=['servers']),
        fqdn=dict(type='str', required=True),
        interface_address=dict(type='str', required=True),
        profile=dict(type='str', default='ADONIS_XMB2', choices=['ADONIS_1200','ADONIS_XMB2']),
        configuration=dict(type='str', required=True),
        friendly_name=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['present','absent']),
        gw_host=dict(type='str', required=True),
        gw_username=dict(type='str', required=True),
        gw_password=dict(type='str', required=True, no_log=True),
        gw_protocol=dict(type='str', default='https', choices=['https','http']),
        gw_apiversion=dict(type='int', default=1)
    )
    # Load Gateway API JSON specification
    api_json = {}
    if os.path.isfile('gateway_api.json'):
        json_data = json.load(open('gateway_api.json'))
        api_json = json_data['resources']
        module_args['resource'] = dict(type='str', required=True, choices=api_json.keys())
    else:
        module_args['resource'] = dict(type='str', required=True)
    
    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        json='',
        status='',
        original_message='',
        msg=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    fetch_args = getparams(module.params)
    #use the transformed module parameters to init the bluecat.py Gateway
    fetch = gwApiCall(module, api_json, **fetch_args)
    #fetch_debug = {'msg':fetch}
    #module.fail_json(**fetch_debug)
    #if a Server Object does not exist it will return a 500 Server Error
    if fetch['status'] <= 204:
        if module.params['state'] == 'present':
            if isdifferent(module, fetch, module.params):
                #update action "patch" is not available in api_json / swagger ui documentation
                update_args = updateparams(module.params)
                fetch = gwApiCall(module, api_json, **update_args)
        else:
            #delete
            delete_args = deleteparams(module.params)
            fetch = gwApiCall(module, api_json, **delete_args)
    else:
        if module.params['state'] == 'present':
            #try to create the resource
            create_args = createparams(module.params)
            fetch = gwApiCall(module, api_json, **create_args)

    module.exit_json(**fetch)
    


def gwApiCall(module, api_json, **gw_args):
    gwresult = {}
    gwresult['changed'] = False
    gwresult['failed'] = False
    gwresult['msg'] = ''
    gw = bluecat.Gateway(api_json, **gw_args)
    try:
        response = gw.invoke(gw_args['resource'], gw_args['action'])
    except Exception as e:
        gw.logout()
        raise e
    else:
        if response.status_code in [201, 204] and not module.check_mode:
            gwresult['changed'] = True
        #capture the original Gateway Json answer
        if not gw_args['action'] == 'delete':
            gwresult['original_message'] = response.json()
        else:
            gwresult['original_message'] = {'msg':'Object Deleted'}
        gwresult['status'] = response.status_code
        if response.status_code >= 400:
            gwresult['msg'] = 'Bad Status Code'
            return gwresult
            #module.fail_json(**gwresult)
            
    return returnparams(module, gwresult)

def returnparams(module, gwresult):
    args = {}
    args['changed'] = gwresult['changed']
    args['msg'] = gwresult['msg']
    args['status'] = gwresult['status']
    args['original_message'] = gwresult['original_message']
    #look for the id and properties key only, and transform them if neccesary
    expectedkeys =['id']
    for k,v in gwresult['original_message'].items():
        if k.lower() == 'name':
            args['friendly_name'] = v
        if k.lower() == 'properties':
            #delimiter | is always present at end of string, so we must ignore the last element (empty)
            l = v.count('|')
            d = dict(x.split('=') for x in v.split('|',l-1))
            for pk,pv in d.items():
                if pk.lower() in ['defaultinterfaceaddress','fullhostname','profile']:
                    if pk.lower() == 'defaultinterfaceaddress':
                        args['interface_address'] = pv.strip('|')
                    if pk.lower() == 'fullhostname':
                        args['fqdn'] = pv.strip('|')
                    if pk.lower() == 'profile':
                        args['profile'] = pv.strip('|')
                else:
                    args[pk] = pv
        if k.lower() in expectedkeys:
            args[k] = v
    return args
    
def getparams(module_args):
    # Load Gateway API JSON specification
    params = {}
    params['resource'] = module_args['resource']
    params['protocol'] = module_args['gw_protocol']
    params['domain'] = module_args['gw_host']
    params['version'] = module_args['gw_apiversion']
    params['username'] = module_args['gw_username']
    params['password'] = module_args['gw_password']
    params['action'] = 'get'
    params['resource_path'] = [{'configuration': module_args['configuration']}, {'server_name':module_args['friendly_name']}]
    params['json_data'] = {}
    return params

def createparams(module_args):
    params = {}
    params['resource'] = module_args['resource']
    params['protocol'] = module_args['gw_protocol']
    params['domain'] = module_args['gw_host']
    params['version'] = module_args['gw_apiversion']
    params['username'] = module_args['gw_username']
    params['password'] = module_args['gw_password']
    params['action'] = 'post'
    params['resource_path'] = [{'configuration': module_args['configuration']}]
    params['json_data'] = { 'fqdn': module_args['fqdn'],
                            'friendly_name': module_args['friendly_name'],
                            'interface_address':module_args['interface_address'],
                            'profile':module_args['profile']
                            }
    return params

def updateparams(module_args):
    params = {}
    params['resource'] = module_args['resource']
    params['protocol'] = module_args['gw_protocol']
    params['domain'] = module_args['gw_host']
    params['version'] = module_args['gw_apiversion']
    params['username'] = module_args['gw_username']
    params['password'] = module_args['gw_password']
    params['action'] = 'patch'
    params['resource_path'] = [{'configuration': module_args['configuration']}, {'view':module_args['view']}]
    params['json_data'] = {'name':module_args['full_zone'],'properties':str('deployable={0}|'.format(module_args['deployable']))}
    return params

def deleteparams(module_args):
    # Load Gateway API JSON specification
    params = {}
    params['resource'] = module_args['resource']
    params['protocol'] = module_args['gw_protocol']
    params['domain'] = module_args['gw_host']
    params['version'] = module_args['gw_apiversion']
    params['username'] = module_args['gw_username']
    params['password'] = module_args['gw_password']
    params['action'] = 'delete'
    params['resource_path'] = [{'configuration': module_args['configuration']}, {'server_name':module_args['friendly_name']}]
    params['json_data'] = {}
    return params

def isdifferent(module, have, want):
    # only look for differences in certain keys
    keysofinterest = ['fqdn','friendly_name','interface_address','profile']
    have_vals = {}
    for k, v in have.items():
        if k in keysofinterest:
            have_vals[k] = v
    want_vals = {}
    for k, v in want.items():
        if k in keysofinterest:
            want_vals[k] = v
    #debug = {'msg':{'want':want_vals, 'have':have_vals}}
    #module.fail_json(**debug)
    #"have": {"configuration": "DE-MCC", "deployable": true, "full_zone": "bluecat3.metro-cc.com|", "view": "internal"}
    #"want": {"configuration": "DE-MCC", "deployable": true, "full_zone": "bluecat3.metro-cc.com", "view": "internal"}
    if have_vals == want_vals:
        return False
    else:
        return True

def main():
    run_module()

if __name__ == '__main__':
    main()