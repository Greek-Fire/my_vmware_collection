# vcenter_helper.py
import atexit
from pyVim import connect
from pyVmomi import vim


class VcenterConnection:
    def __init__(self, host, user, pwd, disable_ssl_verification=False):
        self.host = host
        self.user = user
        self.pwd = pwd
        self.disable_ssl_verification = disable_ssl_verification
        self.si = None

    def connect(self):
        try:
            # Connect to vCenter using SSL or not based on the disable_ssl_verification variable

            if self.disable_ssl_verification:
                service_instance = connect.SmartConnectNoSSL(host=self.host, user=self.user, pwd=self.pwd)
            else:
                service_instance = connect.SmartConnect(host=self.host, user=self.user, pwd=self.pwd)

            # Register atexit to handle disconnecting
                 
            atexit.register(connect.Disconnect, service_instance)
            self.si = service_instance
            return service_instance
        except Exception as e:
            raise Exception(f"Unable to connect to vCenter: {e}")
            
    def disconnect(self):
        try:
            connect.Disconnect(self.si)
        except Exception as e:
            raise Exception(f"Unable to disconnect from vCenter: {e}")

class ContainerViewManager:
    def __init__(self, connection, view_type, recursive):
        self.connection = connection
        self.view_type = view_type
        self.recursive = recursive

    def create_container_view(self):
        try:
            # Create a container view for the specified view type and recursion level

            view = self.connection.content.viewManager.CreateContainerView(self.connection.content.rootFolder, self.view_type, self.recursive)
        except Exception as e:
            raise Exception(f"Could not create container view. Error message:  {e}")
        return view

    def destroy_container_view(self):
        try:
            # Destroy the container view

            self.connection.content.viewManager.DestroyView(self.view)
            print("Container view destroyed successfully")
        except Exception as e:
            raise Exception(f"Could not destroy container view. Error message: {e}")

     def create_property_filter(self, properties):
        try:
            # Create a property filter for the specified properties
            
            property_spec = self.connection.content.propertyCollector.CreatePropertyCollector()
            property_spec.SetCollector(self.view)
            property_spec.SetObjectType(self.view_type)
            property_spec.SetProperties(properties)

            return property_spec
        except Exception as e:
            raise Exception(f"Could not create property filter. Error message: {e}")

class VmFacts:
    def __init__(self, connection):
        self.connection = connection

    def collect_facts(self):

        vm_facts = []
        # Create container view for VirtualMachine
        cv = ContainerViewManager(self.connection, [vim.VirtualMachine], True).create_container_view().view
        
        for vm in cv:
            vm_info = {}
            vm_info['name'] = vm.name
            vm_info['cores'] = vm.config.hardware.numCPU
            vm_info['memory'] = vm.config.hardware.memoryMB
            vm_info['power_state'] = vm.runtime.powerState
            vm_info['vlan'] = None
            vm_info['nic_info'] = []
            vm_info['disk_info'] = []
            vm_info['host'] = None
            vm_info['datastore'] = None
            vm_info['guest_os'] = None
            vm_info['host'] = None
            vm_info['cluster'] = None
            vm_info['datacenter'] = None

            # Grag the vlan
            if vm.network:
                for nic in vm.network.device:
                    if nic.backing.network.name:
                        vm_info['vlan'] = nic.backing.network.name

            
            # Get the vlan infomation
            if vm.network
                for nic in vm.network.device:
                    nic_info = {}
                    nic_info['mac_address'] = device.macAddress
                    nic_info['ip_address'] = device.ipAddress
                    vm_info['nic_info'].append(nic_info)

            # Get the disk infomation
            if vm.storage:
                for disk in vm.storage.perDatastoreUsage:
                    disk_info = {}
                    disk_info['label'] = disk.label
                    disk_info['datastore'] = disk.datastore.name
                    disk_info['disk_size'] = disk.committed
                    vm_info['disk_info'].append(disk_info)

            # Get host and cluster information
            if vm.runtime.host:
                vm_info['host'] = vm.runtime.host.name
                if vm.runtime.host.parent:
                    vm_info['cluster'] = vm.runtime.host.parent.name

            # Get the datacenter information
            if vm.runtime.host.parent:
                if vm.runtime.host.parent.parent:
                    vm_info['datacenter'] = vm.runtime.host.parent.parent.name

       # Destroy the container view
        cv.destroy_container_view()

        return vm_facts

class VlanFacts:
    def __init__(self, connection):
        self.connection = connection

    def collect_facts(self):
        vlan_list = []

        # Create container view for datacenter
        cv = ContainerViewManager(self.connection, [vim.Datacenter], True).create_container_view().view

        # Create property filter to retrieve specific properties
        property_spec = cv.create_property_filter(["network"])

        # Retrieve the datacenter properties
        datacenter_properties = property_spec.RetrieveProperties()

        # Iterate through the datacenters
        for datacenter in datacenter_properties:
            networks = datacenter.network

            # Iterate through the networks in the datacenter
            for network in networks:
                vlan_id = network.config.defaultPortConfig.vlan.vlanId
                vlan_name = network.name
                vlan_dict = {
                    "datacenter": datacenter.name,
                    "vlan_id": vlan_id,
                    "vlan_name": vlan_name,
                    "hosts": [],
                    "clusters": []
                }

                # Get the hosts and clusters in the network
                host_properties = property_spec.RetrieveProperties()

                # Iterate through the hosts
                for host in host_properties:
                    host_name = host.name
                    cluster = host.parent.name

                    if cluster not in vlan_dict["clusters"]:
                        vlan_dict["clusters"].append(cluster)
                    vlan_dict["hosts"].append(host_name)

                vlan_list.append(vlan_dict)

        # Destroy the container view
        view_manager.destroy_container_view()

        return vlan_list

class ClusterFacts:
    def __init__(self, connection):
        self.connection = connection
        self.container_view = ContainerViewManager(self.connection, [vim.ClusterComputeResource], True).create_container_view()
        
    def collect_facts(self):

        cluster_facts = []

        # Create container view for ClusterComputeResource
        cv = ContainerViewManager(self.connection, [vim.ClusterComputeResource], True).create_container_view().view

        # Find all the host clusters in vCenter, and creates a list of dictionaries.

        for cluster in cv:
            cluster_info = {
                'name': cluster.name,
                'hosts': [host.name for host in cluster.host],
                'resource_pool': cluster.resourcePool.name,
                'datacenter': cluster.parent.parent.name,
            }
            cluster_facts.append(cluster_info)

       # Destroy the container view
        cv.destroy_container_view()

        return cluster_facts

class DatastoreClusterFacts:
    def __init__(self, connection):
        self.connection = connection
        
    def collect_facts(self):

        datastore_cluster_facts = []

        # Create container view for Datacenter

        cv = ContainerViewManager(self.connection, [vim.Datacenter], True).create_container_view().view

        # Finds all datastore clusters in vCenter, and creates a list of dictionaries.
    
        for dc in cv:
            for dc in dc.datastoreFolder.childEntity:
                datastore_cluster_info = {
                    'name': dc.name,
                    'capacity': dc.summary.capacity,
                    'datacenter': dc.parent.parent.name,
                    'datastores': [{'name': d.name, 'capacity': d.summary.capacity} for d in dc.childEntity]
                }
                datastore_cluster_facts.append(datastore_cluster_info)
        
        # Sort the datastore clusters by capacity in descending order
        datastore_cluster_facts = sorted(datastore_cluster_facts, key=lambda x: x['capacity'], reverse=True)

       # Destroy the container view
        cv.destroy_container_view()        

        return datastore_cluster_facts