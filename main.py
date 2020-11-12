from dotenv import load_dotenv

load_dotenv()

import os

# Importing keys from .env

ACCESS_KEY_ID = os.getenv("ACCESS_KEY_ID")
SECRET_ACCESS_KEY = os.getenv("SECRET_ACCESS_KEY")

import boto3

# Initializing session

session = boto3.session.Session(
    aws_access_key_id=ACCESS_KEY_ID,
    aws_secret_access_key=SECRET_ACCESS_KEY,
)

ec2 = session.resource(
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

# Creating a new instance

instances = ec2.create_instances(
    ImageId="ami-0885b1f6bd170450c",  # ubuntu 20.04 LTS (HVM)
    MinCount=1,
    MaxCount=1,
    InstanceType="t2.micro",
    KeyName="VerardoKey",
    TagSpecifications=[
        {"ResourceType": "instance", "Tags": [{"Key": "Name", "Value": "VerardoTeste"}]}
    ],
)