import base64
import boto3 # type: ignore
from io import BytesIO
import uuid
from botocore.exceptions import ClientError # type: ignore
from datetime import datetime
import asyncio
import os
from dotenv import load_dotenv # type: ignore



load_dotenv()


aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
region_name = os.getenv("REGION_NAME")


s3_client = boto3.client(
    's3',
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=region_name
)

dynamodb = boto3.resource('dynamodb', region_name=region_name, 
                          aws_access_key_id=aws_access_key, 
                          aws_secret_access_key=aws_secret_key)



def upload_file_to_s3(binary_data, file_name, content_type, bucket_name):

    file_object = BytesIO(binary_data)

    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=file_object,
            ContentType=content_type
        )
        #print(f"File {file_name} uploaded successfully to s3")

    except Exception as e:
        print(f"Error uploading file to the s3 bucket named {bucket_name} with the message: {e}")


#generates unique file name if video is submitted
def generate_file_name():
    unique_name = str(uuid.uuid4())
    return unique_name

#creates unique id for report submitted
def create_unique_id():
    current_year = datetime.now().year
    unique_id = str(current_year) + "-" + "RRDB" + "-" + "1" + str(uuid.uuid4().int)
    """
    eg. 2024-RRDB-109U20U9U2095U209324I450294I5204
    """
    return unique_id

def insert_comment(post_id, author, comment_body):
    try:
        comment_id = create_unique_id()
        comment = {
            'post_id': post_id,
            'author': author,
            'comment_id': comment_id,
            'comment_body': comment_body,
            'created_at': str(datetime.now())
        }
        commentsTable = dynamodb.Table(os.getenv("COMMENTS"))
        commentsTable.put_item(Item=comment)
        print("inserted comment in DB")
    except Exception as e:
        print("could not initialize comments: ", str(e))

#insert report into the DB
def insert_into_db(item_data):

    table = dynamodb.Table(os.getenv("DYNAMODB_TABLE"))

    unique_id = create_unique_id()

    item_data['report_id'] = unique_id
    

    try:
        
        response = table.put_item(Item=item_data)
            
        #print("successfully inserted item into DB")

        
    except ClientError as e:
        print("Error inserting item: ", e.response['Error']['Message'])

def get_all_posts():
    table = dynamodb.Table(os.getenv("DYNAMODB_TABLE"))
    
    response = table.scan()
    items = response.get('Items', [])

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))

    return items

def get_post_by_id(post_id):
    table = dynamodb.Table(os.getenv("DYNAMODB_TABLE"))

    try:
        response = table.get_item(
            Key={
                'report_id': post_id
            }
        )

        if 'Item' in response:
            return response['Item']
        else:
            return None
        
        
    except ClientError as e:
        print(f"Error retrieving item: {e.response['Error']['Message']}")
        pass





