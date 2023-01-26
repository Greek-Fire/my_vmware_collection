import argparse
import paramiko
import subprocess
import re
import os

def is_valid_ip(ip):
    """
    Verifies if the given string is a valid IP address.
    """
    pattern = re.compile(r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$")
    return pattern.match(ip)

def connect(host, user, private_key):
    """
    Connects to the remote host using the specified user and private key.
    """
    if is_valid_ip(host)==None:
        return "This IP is not valid"
    else:
        private_key = paramiko.RSAKey(filename=private_key)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, pkey=private_key)
        return client

def create_playbook():
    """
    Creates an Ansible playbook using the specified module and args.
    """
    playbook = """
    - hosts: all
      tasks:
        - command: "curl 192.168.3.5"
    """
    return playbook

def create_ini(build_host):
    """
    Create tempory inventory file 
    """
    if is_valid_ip(build_host)==None:
        return "This IP is not valid. Only use an ip. Do not use a hostname, or fqdn"

    inventory = f"""
    {build_host}
    """
    return inventory

def create_remote_file(client, file_name, file_path, file_text):
    """
    Create files on execution host
    """
    sftp = client.open_sftp()
    full_path = f"{file_path}/{file_name}"
    with sftp.file(full_path,"w") as f:
        f.write(file_text)
    print(f"{full_path} was created")
    sftp.close()
    
def execute_playbook(client, playbook, host):
    """
    Executes the playbook on the remote host and prints the output.
    """

    # Execute the command and redirect stdout and stderr to a pipe
    stdin, stdout, stderr = client.exec_command(playbook)
    print("Please, wait until the playbook completes. The output will be shown at the end")

    print(stdout.read().decode())
    print(stderr.read().decode())
    print("Ansible Playbook execution completed.")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Runs an Ansible playbook on a remote host.")
    parser.add_argument("--host", help="The host IP address.")
    parser.add_argument("--user", help="The user for the connection.")
    parser.add_argument("--private_key", help="The path to the private key file.")
    parser.add_argument("--build_host", help="the ip address of the host to be built")
    args = parser.parse_args()

    file_path = "/tmp"
    # create connection to execution node
    client = connect(args.host, args.user, args.private_key)

    # Create text to use in playbook file
    playbook_text = create_playbook()

    # Create text to be used in inventory file
    inventory_text = create_ini(args.build_host) 

    # Create files on execution host
    create_playbook = create_remote_file(client, "main.yml", file_path, playbook_text)
    create_ini = create_remote_file(client, "ini", file_path, inventory_text )
    playbook = f"ansible-playbook {file_path}/main.yml -i {file_path}/ini -vvv"
    execute_playbook(client, playbook, args.host)