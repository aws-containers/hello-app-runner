import boto3
from botocore.exceptions import ClientError
import logging
import uuid
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from datetime import datetime
import os

logger = logging.getLogger(__name__)
#dynamoDB=boto3.resource('dynamodb',aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])
dynamoDB=boto3.resource('dynamodb')
yearSeconds=365 * 24 * 3600
def getUser(id, name):
    usrTable = dynamoDB.Table('User') 
    return usrTable.get_item(Key={
                'id': id,
                'name': name
    })

def getScore(id, name):
    usrTable = dynamoDB.Table('User') 
    return usrTable.get_item(Key={
                'id': id,
                'name': name
    })['Item']['score']

def setScore(id, name, score):
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

def insertBlog(title, content, user, photoUrls, timestamp = datetime.now().timestamp()):
    blogTable = dynamoDB.Table('Blog')
    try:
        response = blogTable.put_item(
            Item =
                {
                    'id': str(uuid.uuid4()),
                    'title': title,
                    'content': content,
                    'user': user,
                    'timestamp': timestamp,
                    'photo_urls': photoUrls
                }
            )
    except ClientError as err:
            logger.error(
                "Couldn't insert blog %s in table %s. Here's why: %s: %s",
                title, blogTable.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise

def queryBlogs():
    blogTable = dynamoDB.Table('Blog')
    cutoffTimestamp = datetime.now().timestamp() - yearSeconds
    cutoffTimestampDecimal= Decimal(str(cutoffTimestamp))
    try:
        response = blogTable.query(KeyConditionExpression=Key('timestamp').gt(cutoffTimestampDecimal))
    except ClientError as err:
        logger.error(
            "Couldn't query for blogs published in %s. Here's why: %s: %s", datetime.fromtimestamp(cutoffTimestamp).strftime("s%"),
            err.response['Error']['Code'], err.response['Error']['Message'])
        raise
    else:
        return response['Items']

def scanBlogs():
    blogTable = dynamoDB.Table('Blog')
    blogs = []
    cutoffTimestamp = datetime.now().timestamp() - yearSeconds
    cutoffTimestampDecimal= Decimal(str(cutoffTimestamp))
    scan_kwargs = {
        'FilterExpression': Key('timestamp').gt(cutoffTimestampDecimal)
        #'ProjectionExpression': "#yr, title, info.rating",
        #'ExpressionAttributeNames': {"#yr": "year"}
        }
    try:
        done = False
        start_key = None
        while not done:
            if start_key:
                scan_kwargs['ExclusiveStartKey'] = start_key
            response = blogTable.scan(**scan_kwargs)
            blogs.extend(response.get('Items', []))
            start_key = response.get('LastEvaluatedKey', None)
            done = start_key is None
    except ClientError as err:
            logger.error(
                "Couldn't scan for blogs. Here's why: %s: %s",
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise

    return blogs
#print(setScore('e793419b-17db-4938-a719-db8bcb929225', 'Eric Zhang', 10))