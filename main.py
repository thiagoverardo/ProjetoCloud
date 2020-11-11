from dotenv import load_dotenv

load_dotenv()

import os

ACCESS_KEY_ID = os.getenv("ACCESS_KEY_ID")
SECRET_ACCESS_KEY = os.getenv("SECRET_ACCESS_KEY")

import boto3

ec2 = boto3.client(
    "ec2",
    region_name="us-east-1",
    aws_access_key_id=ACCESS_KEY_ID,
    aws_secret_access_key=SECRET_ACCESS_KEY,
)


instance = ec2.run_instances(
    ImageId="ami-0885b1f6bd170450c",  # ubuntu 20.04 LTS (HVM)
    MinCount=1,
    MaxCount=1,
    InstanceType="t2.micro",
    KeyName="VerardoKey",
    TagSpecifications=[
        {"ResourceType": "instance", "Tags": [{"Key": "Name", "Value": "VerardoTeste"}]}
    ],
)