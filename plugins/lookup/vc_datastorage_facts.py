from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from pyVmomi import vmodl
from pyVmomi import vim
from ansible.module_utils.vcenter_helper import VcenterConnection
from ansible.module_utils.basic import no_log_values

DOCUMENTATION = '''
---
module: vc_datastore_facts
version_added: 1.0.0
short_description: show all content from table
description:
  - This plugin will return the datastore cluster information. It will return the name and storage capacity of the datastore.
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
- name: Get storage facts for the datastore clusters.
  set_fact:
    vms: "{{ lookup('vc_datastore_facts', vcenter='vcenter_hostname', username='username_example', password='password_example', disable_ssl_verification=True) }}"
'''

class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        # Get the vcenter, username, password, and ssl_verification variables passed to the plugin
        vcenter = kwargs.get('vcenter')
        username = kwargs.get('username')
        password = kwargs.get('password')
        disable_ssl_verification = kwargs.get('disable_ssl_verification', False)
        
        datastore_cluster_facts = []
        
        try:
            # Connect to vCenter
            connection = VcenterConnection(vcenter, username, password, disable_ssl_verification)
            si = connection.connect()
        
            # Get the datacenter
            content = si.RetrieveContent()
            datacenters = content.rootFolder.childEntity

            # Iterate over each datacenter
            for datacenter in datacenters:
                # Get the datacenter name
                dc_name = datacenter.name
                # Get the datastores in the current datacenter
                datastores = datacenter.datastoreFolder.childEntity

                # Iterate over each datastore
                for datastore in datastores:
                    # Append a dictionary containing the name, storage and datacenter of the datastore to the 'datastore_cluster_facts' list
                    datastore_cluster_facts.append({'name': datastore.name,'storage': datastore.summary.capacity, 'datacenter': dc_name})

            # Sort the datastore facts by storage capacity in descending order
            datastore_cluster_facts = sorted(datastore_cluster_facts, key=lambda x: x['storage'], reverse=True)

            # Disconnect from vCenter using the vcenter_helper.VcenterConnection class
            vcenter_conn.disconnect()
        except vmodl.MethodFault as e:
            # Raise an error if the connection to vCenter fails
            raise AnsibleError(f"Cannot connect to vCenter: {e.msg}")

        # Hide the password value
        datastore_cluster_facts = no_log_values(datastore_cluster_facts, keys=['password'])
        return datastore_cluster_facts