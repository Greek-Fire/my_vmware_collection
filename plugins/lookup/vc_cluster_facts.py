from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from pyVmomi import vmodl
from pyVmomi import vim
from ansible.module_utils.vcenter_helper import VcenterConnection
from ansible.module_utils.basic import no_log_values

DOCUMENTATION = '''
---
module: vc_cluster_facts
version_added: 1.0.0
short_description: show all content from table
description:
  - This plugin will return the cluster information from a vCenter. It will return the name, number of hosts, resource pool, and datacenter.
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
    vms: "{{ lookup('vc_cluster_facts', vcenter='vcenter_hostname', username='username', password='password', disable_ssl_verification=True) }}"
'''

class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):

        # Get the vcenter, username, password, and ssl_verification variables passed to the plugin
        vcenter = kwargs.get('vcenter')
        username = kwargs.get('username')
        password = kwargs.get('password')
        disable_ssl_verification = kwargs.get('disable_ssl_verification', False)

        # Create an empty list to store the cluster information
        cluster_info = []
        
        try:
            # Connect to vCenter
            connection = VcenterConnection(vcenter, username, password, disable_ssl_verification)
            si = connection.connect()

            # Get the datacenter
            content = si.RetrieveContent()
        
            # Create a container view to retrieve all the ClusterComputeResource objects in the vCenter
            container_view = connection.content.viewManager.CreateContainerView(connection.content.rootFolder, [vim.ClusterComputeResource], True)
            clusters = container_view.view
            container_view.Destroy()
        
            # Iterate through the clusters and store their information in the cluster_info list
            for cluster in clusters:
                cluster_info.append({
                    'name': cluster.name,
                    'hosts': len(cluster.host),
                    'resource_pool': cluster.resourcePool.name,
                    'datacenter': cluster.parent.name
                })
        
            connection.disconnect()
        except vmodl.MethodFault as e:
            # Raise an error if the connection to vCenter fails
            raise AnsibleError(f"Cannot connect to vCenter: {e.msg}")

        # Hide Passsword
        cluster_info = no_log_values(cluster_info, keys=['password'])    
        return cluster_info