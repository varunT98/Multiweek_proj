import boto3

def lambda_handler(event, context):
    ACCESS_KEY = "AKIAY2PSFIV7PQAM2MUE"
    SECRET_KEY = "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"
    AWS_REGION = "us-east-1"
    file = event.get("file")
    topic = event.get("topic")
    sns_client = boto3.client(
        'sns',
        aws_access_key_id = ACCESS_KEY,
        aws_secret_access_key = SECRET_KEY,
        region_name = AWS_REGION)
        
    sns_client.publish(TopicArn = topic, Message = "File Link: " +file,Subject="Please check the file")
        