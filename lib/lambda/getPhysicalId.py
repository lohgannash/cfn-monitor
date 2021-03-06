import json
import cfnresponse
import boto3
from botocore.exceptions import ClientError
import time

def findNestedStack(client,resource):
    if len(resource) == 2:
        return resource
    else:
        max_retries = 20
        sleep_time = 1
        for i in range(max_retries):
            try:
                response = client.list_stack_resources(StackName=resource[0])
            except ClientError as e:
                print e
                time.sleep(sleep_time)
                sleep_time += 1
                continue
            else:
                break
        else:
            return
        for r in response['StackResourceSummaries']:
            if r['ResourceType'] == 'AWS::CloudFormation::Stack':
                if r['LogicalResourceId'] == resource[1]:
                    resource[1] = r['PhysicalResourceId']
        del resource[0]
        return findNestedStack(client,resource)

def findResource(client,resource):
    time.sleep(5)
    if resource:
        max_retries = 20
        sleep_time = 1
        for i in range(max_retries):
            try:
                paginator = client.get_paginator('list_stack_resources')
                page_iterator = paginator.paginate(StackName=resource[0])
                response = []
                for page in page_iterator:
                    response = response + page['StackResourceSummaries']
            except ClientError as e:
                print e
                time.sleep(sleep_time)
                sleep_time += 1
                continue
            else:
                break
        else:
            return
        for r in response:
            if r['LogicalResourceId'] == resource[1]:
                return r['PhysicalResourceId']
    else:
        return

def handler(event, context):
    resource = event['ResourceProperties']['LogicalResourceId'].split(".")
    region = event['ResourceProperties']['Region']
    client = boto3.client('cloudformation',region_name=region)

    responseData = {}
    responseData['PhysicalResourceId'] = findResource(client,findNestedStack(client,resource))
    cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData, "CustomResourcePhysicalID")
    