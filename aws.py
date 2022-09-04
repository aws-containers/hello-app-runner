import boto3
from botocore.exceptions import ClientError
import logging
from decimal import Decimal
import os

logger = logging.getLogger(__name__)
def getUser(id, name):
    dynamoDB=boto3.resource('dynamodb',aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])
    usrTable = dynamoDB.Table('User') 
    return usrTable.get_item(Key={
                'id': id,
                'name': name
    })

def getScore(id, name):
    dynamoDB=boto3.resource('dynamodb',aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])
    usrTable = dynamoDB.Table('User') 
    return usrTable.get_item(Key={
                'id': id,
                'name': name
    })['Item']['score']

def setScore(id, name, score):
    dynamoDB=boto3.resource('dynamodb',aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])
    usrTable = dynamoDB.Table('User')
    try:
            response = usrTable.update_item(
                Key={'id': id, 'name': name},
                UpdateExpression="set score=:r",
                ExpressionAttributeValues={
                    ':r': Decimal(str(score))},
                ReturnValues="UPDATED_NEW")
    except ClientError as err:
            logger.error(
                "Couldn't update score %s in table %s. Here's why: %s: %s",
                score, usrTable.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
    else:
            return response['Attributes']
#print(setScore('e793419b-17db-4938-a719-db8bcb929225', 'Eric Zhang', 10))