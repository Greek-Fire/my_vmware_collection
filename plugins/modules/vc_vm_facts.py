#!/usr/bin/python
from ansible.module_utils.vcenter_helper import VcenterConnection, VmFacts
from ansible.module_utils.basic import AnsibleModule

def main():
    # Define the module's argument specification
    
    module_args = dict(
        vcenter=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        disable_ssl_verification=dict(type='bool', default=False)
    )

    # Create a new Ansible module
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    # Create a connection to vCenter
    connection = VcenterConnection(module.params['vcenter'],
                                  module.params['username'],
                                  module.params['password'],
                                  module.params['disable_ssl_verification'])
    connection.connect()

    # Collect vm facts using the VmFacts class
    vm_facts = VmFacts(connection).collect_facts()

    # Disconnect from vCenter
    connection.disconnect()

    # Return the vm facts in the Ansible module's exit json
    module.exit_json(changed=False, vm_facts=vm_facts)

if __name__ == '__main__':
    main()