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
            if self.disable_ssl_verification:
                service_instance = connect.SmartConnectNoSSL(host=self.host, user=self.user, pwd=self.pwd)
            else:
                service_instance = connect.SmartConnect(host=self.host, user=self.user, pwd=self.pwd)
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
            view = self.connection.content.viewManager.CreateContainerView(self.connection.content.rootFolder, self.view_type, self.recursive)
        except Exception as e:
            raise Exception(f"Could not create container view. Error message:  {e}")
        return view

class VmFacts:
    def __init__(self, connection):
        self.connection = connection
        self.container_view = ContainerViewManager(self.connection, [vim.VirtualMachine], True).create_container_view()
        self.vm_facts = []

    def collect_facts(self):
        vms = self.container_view.view
        for vm in vms:
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

        return self.vm_facts


class VlanFacts:
    def __init__(self, connection):
        self.connection = connection
        self.container_view = ContainerViewManager(self.connection, [vim.Datacenter], True).create_container_view()
        self.vlans = []

    def collect_facts(self):       

        # Retrieve vlan information for all datacenters
        vlan_properties = ["name"]
        vlan_data = self.connection.content.propertyCollector.RetrieveProperties(self.container_view, vlan_properties)

        # Iterate through vlan data and store relevant information
        for vlan in vlan_data:
            vlan_info = {}
            vlan_info["name"] = vlan.name

            # Get cluster information
            if vlan.host and vlan.host.parent:
                vlan_info["cluster"] = vlan.host.parent.name

            # Get datacenter information
            if vlan.host and vlan.host.parent:
                if vlan.host.parent.parent:
                    vlan_info["datacenter"] = vlan.host.parent.parent.name
            vlans.append(vlan_info)

        return self.vlans

class ClusterFacts:
    def __init__(self, connection):
        self.connection = connection
        self.container_view = ContainerViewManager(self.connection, [vim.ClusterComputeResource], True).create_container_view()
        self.cluster_facts = []
        
    def collect_facts(self):
        # Find all the host clusters in vCenter, and creates a list of dictionaries.

        for cluster in self.container_view.view:
            cluster_info = {}
            cluster_info['name'] = cluster.name
            cluster_info['hosts'] = [host.name for host in cluster.host]
            cluster_info['resource_pool'] = cluster.resourcePool.name
            cluster_info['datacenter'] = cluster.parent.parent.name
            self.cluster_facts.append(cluster_info)
        return self.cluster_facts

class DatastoreClusterFacts:
    def __init__(self, connection):
        self.connection = connection
        self.container_view = ContainerViewManager(self.connection, [vim.Datacenter], True).create_container_view()
        self.datastore_cluster_facts = []
        
    def collect_facts(self):
        # Finds all datastore clusters in vCenter, and creates a list of dictionaries.
    
        for dc in self.container_view.view:
            for datastore_cluster in dc.datastoreFolder.childEntity:
                datastore_cluster_info = {}
                datastore_cluster_info['name'] = datastore_cluster.name
                datastore_cluster_info['capacity'] = datastore_cluster.summary.capacity
                datastore_cluster_info['datacenter'] = dc.name
                datastore_cluster_info['datastores'] = []
                for datastore in datastore_cluster.childEntity:
                    datastore_cluster_info['datastores'].append({'name': datastore.name, 'capacity': datastore.summary.capacity})
                self.datastore_cluster_facts.append(datastore_cluster_info)
        
        # Sort the datastore clusters by capacity in descending order
        self.datastore_cluster_facts = sorted(self.datastore_cluster_facts, key=lambda x: x['capacity'], reverse=True)

        return self.datastore_cluster_facts