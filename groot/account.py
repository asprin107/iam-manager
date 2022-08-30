import boto3
import botocore.client
import re


class Account:
    session: boto3.Session
    client: botocore.client

    def __init__(self, session: boto3.Session):
        self.client = session.client('sts')

    def get_aws_account_info(self):
        """
        Get AWS Account information

        :return:
        {
            'Account': {AWS_ACCOUNT_ID},
            'UserArn': 'arn:aws:iam::{ACCOUNT_ID}:user/{IAM_USER_NAME}'
            'UserName': '{IAM_USER_NAME}'
        }
        """
        result = {}
        aws_account_info = self.client.get_caller_identity()
        result['UserArn'] = aws_account_info['Arn']
        user_name = re.sub(r'arn:aws:iam::+[0-9]*:user', '', result['UserArn'])  # Delete 'arn:aws:iam::{ACCOUNT_ID}:user'
        user_name = user_name.split('/')[-1]  # Remove path, get user name only
        result['UserName'] = user_name
        result['Account'] = aws_account_info['Account']
        return result
