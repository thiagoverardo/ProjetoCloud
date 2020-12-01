from dotenv import load_dotenv

load_dotenv()

import os

# Importing keys from .env

ACCESS_KEY_ID = os.getenv("ACCESS_KEY_ID")
SECRET_ACCESS_KEY = os.getenv("SECRET_ACCESS_KEY")

import boto3
import time
import requests

# Initializing session in Ohio
print("===================================================================")
print("================ Initializing sessions and clients ================")
print("===================================================================\n")


session = boto3.session.Session(
    aws_access_key_id=ACCESS_KEY_ID,
    aws_secret_access_key=SECRET_ACCESS_KEY,
)

ec2 = session.resource(
    "ec2",
    region_name="us-east-2",  # ohio
)

# Clients are similar to resources but operate at a lower level of abstraction
client = session.client(
    "ec2",
    region_name="us-east-2",
)

session_nv = boto3.session.Session(
    aws_access_key_id=ACCESS_KEY_ID,
    aws_secret_access_key=SECRET_ACCESS_KEY,
)

ec2_nv = session_nv.resource(
    "ec2",
    region_name="us-east-1",  # NV
)

# Clients are similar to resources but operate at a lower level of abstraction
client_nv = session_nv.client(
    "ec2",
    region_name="us-east-1",
)

client_lb = session_nv.client("elb", region_name="us-east-1")

client_asg = session_nv.client("autoscaling", region_name="us-east-1")

print("============= Terminating existing autoscaling group =============\n")

try:
    response_asg = client_asg.describe_auto_scaling_groups(
        AutoScalingGroupNames=[
            "ASG_NV",
        ],
    )

    if len(response_asg["AutoScalingGroups"]) > 0:
        delete_asg = response_asg["AutoScalingGroups"][0]["AutoScalingGroupName"]
        response_asg_delete = client_asg.delete_auto_scaling_group(
            AutoScalingGroupName=delete_asg,
            ForceDelete=True,
        )

        delete_lc = client_asg.delete_launch_configuration(
            LaunchConfigurationName="ASG_NV"
        )
    else:
        print("No asg to delete\n")

except:
    print("No asg to delete\n")


print("============= Terminating existing load balancer =============\n")

try:
    response_lb = client_lb.describe_load_balancers(
        LoadBalancerNames=[
            "ThiagoLB",
        ],
    )

    delete_lb = response_lb["LoadBalancerDescriptions"][0]["LoadBalancerName"]
    response_lb_delete = client_lb.delete_load_balancer(LoadBalancerName=delete_lb)

except:
    print("No load balancer to terminate\n")

print("============= Terminating existing instances =============\n")

# Filtering and terminating running instances

try:
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
            waiter = client.get_waiter("instance_terminated")
            client.terminate_instances(InstanceIds=[i.id])
            waiter.wait(InstanceIds=[i.id])
            print("Instance {0} terminated\n".format(i.id))

    else:
        print("No instances to terminate\n")

except:
    print("No instances to terminate\n")

print("=============================================================================")
print("============= Initializing session and client in North Virginia =============")
print("=============================================================================\n")

print("====================== Terminating existing instances =======================\n")

# Filtering and terminating running instances
try:
    instances_filter_nv = ec2_nv.instances.filter(
        Filters=[
            {"Name": "instance-state-name", "Values": ["running"]},
            {"Name": "tag:Name", "Values": ["NVVerardo"]},
        ]
    )

    instances_running_nv = []
    for i in instances_filter_nv:
        instances_running_nv.append(i.id)

    if len(instances_running_nv) > 0:
        for i in instances_filter_nv:
            waiter_nv = client_nv.get_waiter("instance_terminated")
            client_nv.terminate_instances(InstanceIds=[i.id])
            waiter_nv.wait(InstanceIds=[i.id])
            print("Instance {0} terminated\n".format(i.id))

    else:
        print("No instances to terminate\n")
except:
    print("No instances to terminate\n")

print("============= Terminating existing security groups =============\n")
# Filtering and terminating existing security groups
try:
    for ohio_security_group in client.describe_security_groups()["SecurityGroups"]:
        if ohio_security_group["GroupName"] == "Ohio_SG":
            response_sg1 = client.delete_security_group(GroupName="Ohio_SG")
            print("SG {0} terminated\n".format(ohio_security_group["GroupId"]))
except:
    print("No security groups to terminate\n")

try:
    for nv_security_group in client_nv.describe_security_groups()["SecurityGroups"]:
        if nv_security_group["GroupName"] == "NV_SG":
            response_sg_nv1 = client_nv.delete_security_group(GroupName="NV_SG")
            print("SG {0} terminated\n".format(nv_security_group["GroupId"]))
except:
    print("No security groups to terminate\n")

print("============= Creating instance initialization with ORM =============\n")

print("============= Creating instance initialization database =============\n")

# Creating the first instance initialization settings with postgresql (localhost 5432)
h2_postgres = """#!/bin/bash
sudo apt update
sudo apt install postgresql postgresql-contrib -y
sudo -u postgres psql -c "CREATE USER cloud WITH PASSWORD 'cloud';"
sudo -u postgres psql -c "CREATE DATABASE tasks OWNER cloud;"
sudo sed -i "59 c listen_addresses = '*'" /etc/postgresql/12/main/postgresql.conf
sudo bash -c 'echo "host all all 0.0.0.0/0 trust" >> /etc/postgresql/12/main/pg_hba.conf'
sudo ufw allow 5432/tcp
sudo systemctl restart postgresql
"""

print("============= Creating Ohio Security Group =============\n")

# Security Group
Ohio_SG = client.create_security_group(
    GroupName="Ohio_SG", Description="Security group of ohio"
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
print("Ingress Successfully Set\n")

print("=============================================================================")
print("============================= Creating instance =============================")
print("=============================================================================\n")

try:
    response_key = client.describe_key_pairs(
        KeyNames=[
            "KeyTeste",
        ],
    )

    # Deleting Keypair
    if len(response_key["KeyPairs"]) > 0:
        response_key_delete = client.delete_key_pair(
            KeyName="KeyTeste",
        )
        print("Deleted keypair")

    # Creating Keypair
    response_key_create = client.create_key_pair(
        KeyName="KeyTeste",
    )
except:
    response_key_create = client.create_key_pair(
        KeyName="KeyTeste",
    )

# Creating the first instance (ohio)
instance = ec2.create_instances(
    ImageId="ami-0a91cd140a1fc148a",  # ubuntu 20.04 LTS (HVM)
    MinCount=1,
    MaxCount=1,
    InstanceType="t2.micro",
    KeyName="KeyTeste",
    UserData=h2_postgres,
    SecurityGroups=["Ohio_SG"],
    TagSpecifications=[
        {"ResourceType": "instance", "Tags": [{"Key": "Name", "Value": "VerardoTeste"}]}
    ],
)[0]

print("Waiting until instance is running\n")

instance.wait_until_running()
instance.reload()
print(instance.state)
print("\n")
public_ip_ohio = instance.public_ip_address

# ===============================================================================
# Creating another instance in North Virginia to connect with the ohio's database
# ===============================================================================

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

print("============= Creating North Virginia Security Group =============\n")

# Security Group
NV_SG = client_nv.create_security_group(
    GroupName="NV_SG", Description="Security group of north virginia"
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
print("Ingress Successfully Set {0}\n".format(data_nv))

print("=============================================================================")
print("============================ Creating instance 2 ============================")
print("=============================================================================\n")

try:
    response_key_nv = client_nv.describe_key_pairs(
        KeyNames=[
            "KeyTesteNV",
        ],
    )
    # Deleting Keypair
    if len(response_key_nv["KeyPairs"]) > 0:
        response_key_delete_nv = client_nv.delete_key_pair(
            KeyName="KeyTesteNV",
        )

    # Creating Keypair
    response_key_create_nv = client_nv.create_key_pair(
        KeyName="KeyTesteNV",
    )
except:
    response_key_create_nv = client_nv.create_key_pair(
        KeyName="KeyTesteNV",
    )

# Creating instance (ohio)
instance_nv = ec2_nv.create_instances(
    ImageId="ami-0885b1f6bd170450c",  # ubuntu 20.04 LTS (HVM)
    MinCount=1,
    MaxCount=1,
    InstanceType="t2.micro",
    KeyName="KeyTesteNV",
    UserData=h2_ORM,
    SecurityGroups=["NV_SG"],
    TagSpecifications=[
        {
            "ResourceType": "instance",
            "Tags": [{"Key": "Name", "Value": "NVVerardo"}],
        }
    ],
)[0]

print("Waiting until instance is running\n")

instance_nv.wait_until_running()
instance_nv.reload()
print(instance_nv.state)
print(instance_nv.public_ip_address)
print("\n")

print("============= Creating load balancer =============\n")

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

print("============= Creating autoscaling group =============\n")

id_TG_LB = client_lb.describe_load_balancers(
    LoadBalancerNames=[
        "ThiagoLB",
    ],
)

print(instance_nv.id)

response_asg = client_asg.create_auto_scaling_group(
    AutoScalingGroupName="ASG_NV",
    InstanceId=instance_nv.id,
    MinSize=1,
    MaxSize=5,
    LoadBalancerNames=[
        "ThiagoLB",
    ],
    Tags=[{"Key": "Name", "Value": "ASG_NV_INSTANCE"}],
)

response_attach_lb = client_asg.attach_load_balancers(
    AutoScalingGroupName="ASG_NV",
    LoadBalancerNames=[
        "ThiagoLB",
    ],
)

print("=============================================================================")
print("============================= Creating requests =============================")
print("=============================================================================\n")

dnsLB = response_lb["DNSName"]
print("LB url {0}".format(dnsLB))
dnsLB_str = '"http://{0}:8080/tasks/"'.format(dnsLB)
print(dnsLB_str)

with open("client.py", "r") as f:
    file = f.readlines()
    file[4] = "urlLB =" + dnsLB_str + "\n"
    file[5] = "\n"

with open("client.py", "w") as f:
    f.writelines(file)
    print(file)
