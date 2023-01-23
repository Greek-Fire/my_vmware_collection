from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from pyVmomi import vmodl
from pyVmomi import vim
from ansible.module_utils.vcenter_helper import VcenterConnection
from ansible.module_utils.basic import no_log_values

DOCUMENTATION = '''
---
module: vc_vm_facts
version_added: 1.0.0
short_description: show all content from table
description:
  - This plugin will return vm information for every vm. It will return the name, host, cluster, datacenter, power state, disk info, and nic info.
author:
  - "Louis Tiches"
options:
  vcenter:
    description: Add the vcenter your would like to communicate with
    required: true
    type: str
  username:
    description: Add your vcenter username
    required: true
    type: str
  password:
    description: Add your vcenter password
    required: true
    type: str
  disable_ssl_verification:
    description: Disable SSL verification
    required: false
    type: bool

'''

EXAMPLES = '''
- name: Get vm information
  set_fact:
    vms: "{{ lookup('vc_vm_facts', vcenter='vcenter_hostname', username='username', password='password', disable_ssl_verification=True) }}"
'''

class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        vcenter = kwargs.get('vcenter')
        username = kwargs.get('username')
        password = kwargs.get('password')
        disable_ssl_verification = kwargs.get('disable_ssl_verification', False)
        host_facts = []

        try:
             # Connect to vCenter
            connection = VcenterConnection(vcenter, username, password, disable_ssl_verification)
            si = connection.connect()

            # Get the vm information
            container_view = connection.content.viewManager.CreateContainerView(connection.content.rootFolder, [vim.VirtualMachine], True)
            for vm in container_view.view:
                host_dict = {}
                host_dict['name'] = vm.name
                host_dict['host'] = vm.summary.runtime.host.name
                host_dict['cluster'] = vm.summary.runtime.host.parent.name
                host_dict['datacenter'] = vm.summary.runtime.host.parent.parent.name
                host_dict['power_state'] = vm.summary.runtime.powerState
                
                # Collect host disk information
                host_dict['disk_info'] = []
                for disk in vm.config.hardware.device:
                    if isinstance(disk, vim.vm.device.VirtualDisk):
                        host_dict['disk_info'].append({'disk_label': disk.deviceInfo.label, 'disk_size': disk.capacityInKB})
                        
                # Collect host nic information
                host_dict['nic_info'] = []
                for nic in vm.config.hardware.device:
                    if isinstance(nic, vim.vm.device.VirtualEthernetCard):
                        host_dict['nic_info'].append({'nic_label': nic.deviceInfo.label, 'mac_address': nic.macAddress})

                host_facts.append(host_dict)

            connection.disconnect()
        except vmodl.MethodFault as e:
            raise AnsibleError(f"Cannot connect to vCenter: {e.msg}")

        return host_facts
