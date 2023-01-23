from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from pyVmomi import vmodl
from pyVmomi import vim
from ansible.module_utils.vcenter_helper import VcenterConnection
from ansible.module_utils.basic import no_log_values

DOCUMENTATION = '''
---
module: vc_vlan_facts
version_added: 1.0.0
short_description: show useful vlan facts
description:
  - This plugin will return the vlan information from a each cluster. It will return a nested dictionary with the cluster name and the vlan id and host name and the vlan id.
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
- name: Get vlan facts
  set_fact:
    vms: "{{ lookup('vc_vlan_facts', vcenter='vcenter', username='username, password='password', disable_ssl_verification=True) }}"
'''

class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        vcenter = kwargs.get('vcenter')
        username = kwargs.get('username')
        password = kwargs.get('password')
        disable_ssl_verification = kwargs.get('disable_ssl_verification', False)
        vlans = []
        
        try:
            # Connect to vCenter
            connection = VcenterConnection(vcenter, username, password, disable_ssl_verification)
            si = connection.connect()
            
            # Get the datacenter
            content = si.RetrieveContent()
            datacenters = content.rootFolder.childEntity

            
            for datacenter in datacenters:
                # Get the clusters in the current datacenter
                clusters = datacenter.hostFolder.childEntity
                
                for cluster in clusters:
                    # Get the vlans in the current cluster
                    for network in cluster.network:
                        vlans.append({'vlan_name': network.name, 'cluster': cluster.name, 'datacenter': datacenter.name})

            # Disconnect from vCenter using the vcenter_helper.VcenterConnection class
            connection.disconnect()
        except vmodl.MethodFault as e:
            # Raise an error if the connection to vCenter fails
            raise AnsibleError(f"Cannot connect to vCenter: {e.msg}")
        
        return vlans
