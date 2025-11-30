import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("create_service_provider invoked")
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from create_service_provider!')
    }
