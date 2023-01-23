from ansible.module_utils.basic import AnsibleModule
from pyVim import connect
from pyVmomi import vmodl

class VcenterConnection:

    def __init__(self, module):
        # Initialize the vCenter connection object with the provided Ansible module
        self.module = module
        self.vcenter = module.params['vcenter']
        self.username = module.params['username']
        self.password = module.params['password']
        self.disable_ssl_verification = module.params.get('disable_ssl_verification', False)

    def connect(self):
        # Connect to the vCenter and return the service instance object
        try:
            si = connect.SmartConnect(
                host=self.vcenter,
                user=self.username,
                pwd=self.password,
                sslContext=sslContext() if self.disable_ssl_verification else None
            )
            return si
        except vmodl.MethodFault as e:
            self.module.fail_json(msg=f"Cannot connect to vCenter: {e.msg}")

    def disconnect(self):
        # Disconnect from the vCenter
        connect.Disconnect(si)

def sslContext():
    # Create a new SSL context with the default options and disable certificate verification
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context