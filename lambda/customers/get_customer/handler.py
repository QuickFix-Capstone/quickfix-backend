import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("get_customer invoked")
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from get_customer!')
    }
