from dotenv import load_dotenv

load_dotenv()

import os

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
        print("Instance {0} terminated".format(i.id))

else:
    print("No instances to terminate")

# Creating the first instance initialization settings with postgresql (localhost 5432)

h2_postgres = """#!/bin/bash
sudo apt update
sudo apt install postgresql postgresql-contrib -y
sudo -u postgres psql -c "CREATE USER cloud WITH PASSWORD 'cloud';"
sudo -u postgres psql -c "CREATE DATABASE test OWNER cloud;"
sudo sed -i "59 c\
listen_addresses = '*'" /etc/postgresql/12/main/postgresql.conf
sudo bash -c 'echo "host all all 0.0.0.0/0 trust" >> /etc/postgresql/12/main/pg_hba.conf'
sudo ufw allow 5432/tcp
sudo systemctl restart postgresql
"""

# Security Group
Ohio_SG = ec2.create_security_group(
    GroupName="Ohio_SG", Description="Security group of ohio's database"
)

data = client.authorize_security_group_ingress(
    GroupId=Ohio_SG["GroupId"],
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
        {
            "IpProtocol": "tcp",
            "FromPort": 5432,
            "ToPort": 5432,
            "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
        },
    ],
)
print("Ingress Successfully Set %s" % data)

# Creating the first instance (ohio)
instances = ec2.create_instances(
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
)

for i in instances:
    print("instance {0} created".format(i.id))

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

# Filtering and terminating running instances

instances_filter_nv = ec2_nv.instances.filter(
    Filters=[
        {"Name": "instance-state-name", "Values": ["running"]},
        {"Name": "tag:Name", "Values": ["VerardoTeste"]},
    ]
)

instances_running_nv = []
for i in instances_filter_nv:
    instances_running_nv.append(i.id)

if len(instances_running_nv) > 0:
    for i in instances_filter_nv:
        ec2_nv.Instance(i.id).terminate()
        print("Instance {0} terminated".format(i.id))

else:
    print("No instances to terminate")

# Creating the first instance initialization settings with postgresql (localhost 5432)

h2_ORM = """#!/bin/bash
maas login cloudt http://192.168.0.3:5240/MAAS/
token
maas cloudt machines allocate name=node2
maas cloudt machine deploy [system_id]
ssh ubuntu@node2:192.168.0.3:5240
cd task/./install.sh
reboot
wget http://[IP node2]:8080/admin/
"""

# # Creating the firs instance (ohio)

instances_nv = ec2_nv.create_instances(
    ImageId="ami-0885b1f6bd170450c",  # ubuntu 20.04 LTS (HVM)
    MinCount=1,
    MaxCount=1,
    InstanceType="t2.micro",
    KeyName="VerardoKey",
    UserData=h2_ORM,
    TagSpecifications=[
        {"ResourceType": "instance", "Tags": [{"Key": "Name", "Value": "VerardoTeste"}]}
    ],
)


for i in instances_nv:
    print("instance {0} created".format(i.id))
