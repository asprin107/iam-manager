from datetime import datetime, timezone

import boto3

from groot import Service
from groot.secure import Secure
import json

lambda_profile = boto3.Session


def decrypt_with_kms(client_data: bytes):
    secure = Secure(lambda_profile)
    return secure.decrypt(client_data)


def lambda_handler(event, context):
    key = json.loads(decrypt_with_kms(bytes(context.client_context.custom['key'], 'utf-8')))
    service = Service(
        access_key_id=key['aws_access_key_id'],
        secret_access_key=key['aws_secret_access_key']
    )

    request_type = context.client_context.custom['request_type']

    functions = {
        'publish_credential': publish_credential,
        'delete_credential': delete_credential,
        'check_credential': check_credential,
        'remove_inactive_credential': remove_inactive_credential,
        'mark_inactive_older_credential': mark_inactive_older_credential
    }

    response = functions[request_type]
    return response


# TODO implement
def publish_credential():
    pass


# TODO implement
def delete_credential():
    pass


# TODO implement
def check_credential():
    pass


# TODO implement
def remove_inactive_credential():
    pass


# TODO implement
def mark_inactive_older_credential():
    pass
