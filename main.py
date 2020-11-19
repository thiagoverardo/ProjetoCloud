from dotenv import load_dotenv

load_dotenv()

import os
import time

# Importing keys from .env

ACCESS_KEY_ID = os.getenv("ACCESS_KEY_ID")
SECRET_ACCESS_KEY = os.getenv("SECRET_ACCESS_KEY")

import boto3
from botocore.exceptions import ClientError

# Initializing session in Ohio

session = boto3.session.Session(
    aws_access_key_id=ACCESS_KEY_ID,
    aws_secret_access_key=SECRET_ACCESS_KEY,
)

ec2 = session.resource(
    "ec2",
    region_name="us-east-1",  # para testar está em NV
)

# Clients are similar to resources but operate at a lower level of abstraction
client = session.client(
    "ec2",
    region_name="us-east-1",
)

# Filtering and terminating running instances

instances_filter = ec2.instances.filter(
    Filters=[
        {"Name": "instance-state-name", "Values": ["running"]},
        {"Name": "tag:Name", "Values": ["VerardoTeste"]},
    ]
)

instances_running = []
for i in instances_filter:
    instances_running.append(i.id)

if len(instances_running) > 0:
    for i in instances_filter:
        ec2.Instance(i.id).terminate()
        waiter = client.get_waiter("instance_terminated")
        waiter.wait(InstanceIds=[i.id])
        print("Instance {0} terminated".format(i.id))

else:
    print("No instances to terminate")

# Filtering and terminating existing security groups
response_sg = client.describe_security_groups(
    GroupNames=[
        "Ohio_SG",
    ],
)
if response_sg:
    print("Terminating Ohio_SG security group")
    response_sg1 = client.delete_security_group(GroupName="Ohio_SG")
else:
    print("No security groups to terminate")

# Creating the first instance initialization settings with postgresql (localhost 5432)
h2_postgres = """#!/bin/bash
sudo apt update
sudo apt install postgresql postgresql-contrib -y
sudo -u postgres psql -c "CREATE USER cloud WITH PASSWORD 'cloud';"
sudo -u postgres psql -c "CREATE DATABASE tasks OWNER cloud;"
sudo sed -i "59 c\
listen_addresses = '*'" /etc/postgresql/12/main/postgresql.conf
sudo bash -c 'echo "host all all 0.0.0.0/0 trust" >> /etc/postgresql/12/main/pg_hba.conf'
sudo ufw allow 5432/tcp
sudo systemctl restart postgresql
"""

# Security Group
Ohio_SG = client.create_security_group(
    GroupName="Ohio_SG", Description="Security group of ohios database"
)

data = client.authorize_security_group_ingress(
    GroupId=Ohio_SG["GroupId"],
    IpPermissions=[
        {
            "IpProtocol": "tcp",
            "FromPort": 22,
            "ToPort": 22,
            "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
        },
        {
            "IpProtocol": "tcp",
            "FromPort": 5432,
            "ToPort": 5432,
            "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
        },
    ],
)
print("Ingress Successfully Set {0}".format(data))

# Creating the first instance (ohio)
instance = ec2.create_instances(
    ImageId="ami-0885b1f6bd170450c",  # ubuntu 20.04 LTS (HVM)
    MinCount=1,
    MaxCount=1,
    InstanceType="t2.micro",
    KeyName="VerardoKey",
    UserData=h2_postgres,
    SecurityGroups=["Ohio_SG"],
    TagSpecifications=[
        {"ResourceType": "instance", "Tags": [{"Key": "Name", "Value": "VerardoTeste"}]}
    ],
)[0]

print("Waiting until instance is running")

instance.wait_until_running()
instance.reload()
print(instance.state)
public_ip_ohio = instance.public_ip_address

# Creating another instance in North Virginia to connect with the ohio's database

# Initializing session in North Virginia
session_nv = boto3.session.Session(
    aws_access_key_id=ACCESS_KEY_ID,
    aws_secret_access_key=SECRET_ACCESS_KEY,
)

ec2_nv = session_nv.resource(
    "ec2",
    region_name="us-east-1",  # NV
)

# Clients are similar to resources but operate at a lower level of abstraction
client_nv = session.client(
    "ec2",
    region_name="us-east-1",
)

# Filtering and terminating running instances
instances_filter_nv = ec2_nv.instances.filter(
    Filters=[
        {"Name": "instance-state-name", "Values": ["running"]},
        {"Name": "tag:Name", "Values": ["VerardoTesteNV"]},
    ]
)

instances_running_nv = []
for i in instances_filter_nv:
    instances_running_nv.append(i.id)

if len(instances_running_nv) > 0:
    for i in instances_filter_nv:
        ec2_nv.Instance(i.id).terminate()
        waiter = client_nv.get_waiter("instance_terminated")
        waiter.wait(InstanceIds=[i.id])
        print("Instance {0} terminated".format(i.id))

else:
    print("No instances to terminate")

# Filtering and terminating existing security groups
response_sg_nv = client.describe_security_groups(
    GroupNames=[
        "NV_SG",
    ],
)
if response_sg_nv:
    print("Terminating NV_SG security group")
    response_sg_nv1 = client.delete_security_group(GroupName="NV_SG")
else:
    print("No security groups to terminate")

# Creating the first instance initialization settings

h2_ORM = f"""#!/bin/bash
sudo apt update
cd /home/ubuntu/
git clone https://github.com/thiagoverardo/tasks
sudo sed -i "83 c 'HOST': '{public_ip_ohio}'," ./tasks/portfolio/settings.py
cd ./tasks
sh ./install.sh
sudo reboot
"""
# Security Group
NV_SG = client_nv.create_security_group(
    GroupName="NV_SG", Description="Security group of north virginia database"
)

data_nv = client_nv.authorize_security_group_ingress(
    GroupId=NV_SG["GroupId"],
    IpPermissions=[
        {
            "IpProtocol": "tcp",
            "FromPort": 8080,
            "ToPort": 8080,
            "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
        },
        {
            "IpProtocol": "tcp",
            "FromPort": 22,
            "ToPort": 22,
            "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
        },
    ],
)
print(f"Ingress Successfully Set {data_nv}")

# Creating instance (ohio)

instance_nv = ec2_nv.create_instances(
    ImageId="ami-0885b1f6bd170450c",  # ubuntu 20.04 LTS (HVM)
    MinCount=1,
    MaxCount=1,
    InstanceType="t2.micro",
    KeyName="VerardoKey",
    UserData=h2_ORM,
    SecurityGroups=["NV_SG"],
    TagSpecifications=[
        {
            "ResourceType": "instance",
            "Tags": [{"Key": "Name", "Value": "VerardoTesteNV"}],
        }
    ],
)[0]


instance_nv.wait_until_running()
instance_nv.reload()
print(instance_nv.state)
print(instance_nv.public_ip_address)

client_lb = session_nv.client("elb", region_name="us-east-1")

try:
    response_lb_delete = client.delete_load_balancer(LoadBalancerName="ThiagoLB")
except:
    print("no lb to delete")

id_SG = client_nv.describe_security_groups(
    GroupNames=[
        "NV_SG",
    ],
)

response_lb = client_lb.create_load_balancer(
    LoadBalancerName="ThiagoLB",
    Listeners=[
        {
            "Protocol": "TCP",
            "LoadBalancerPort": 8080,
            "InstanceProtocol": "TCP",
            "InstancePort": 8080,
        },
    ],
    SecurityGroups=[
        id_SG["SecurityGroups"][0]["GroupId"],
    ],
    AvailabilityZones=[
        "us-east-1a",
        "us-east-1b",
        "us-east-1c",
        "us-east-1d",
        "us-east-1e",
        "us-east-1f",
    ],
)
