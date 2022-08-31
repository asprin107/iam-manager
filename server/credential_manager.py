from datetime import datetime, timezone

import boto3

from groot import Service
from groot.secure import Secure
import json

lambda_profile = boto3.Session
kms_key: str


def response_value(msg: str, data):
    response_payload = {
        "msg": msg,
        "data": data
    }
    encrypt_with_kms(json.dumps(response_payload), key_id=key_id)
    return


def publish_credential(service: Service, user_name: str):
    return response_value(
        msg="Publish a new Credential",
        data=service.publish_new_credential(user_name=user_name)
    )


def delete_credential(service: Service, user_name: str, access_key_id: str):
    return response_value(
        msg="",
        data=service.delete_credential(user_name=user_name, access_key_id=access_key_id)
    )


def check_credential(service: Service, user_name: str):
    return response_value(
        msg="",
        data=service.need_to_publish_new_credential(user_name=user_name)
    )


def remove_inactive_credential(service: Service, user_name: str):
    return response_value(
        msg="",
        data=service.remove_inactive_credential(user_name=user_name)
    )


def mark_inactive_older_credential(service: Service, user_name: str):
    return response_value(
        msg="",
        data=service.mark_inactive_older_credential(user_name=user_name)
    )


def decrypt_with_kms(client_data: bytes, key_id: str):
    secure = Secure(lambda_profile)
    return secure.decrypt(client_data, key_id)


def encrypt_with_kms(server_data: str, key_id: str):
    secure = Secure(lambda_profile)
    return secure.encrypt(server_data, key_id)


def lambda_handler(event, context):
    key = json.loads(
        decrypt_with_kms(
            client_data=bytes(context.client_context.custom['key'], 'utf-8'),
            key_id=context.client_context.custom['key_alias']  # kms key id
        )
    )
    service = Service(
        access_key_id=key['aws_access_key_id'],
        secret_access_key=key['aws_secret_access_key']
    )

    request_type = context.client_context.custom['request_type']

    functions = {
        'publish_credential': publish_credential(service, user_name),
        'delete_credential': delete_credential(service, user_name, access_key_id),
        'check_credential': check_credential(service, user_name),
        'remove_inactive_credential': remove_inactive_credential(service, user_name),
        'mark_inactive_older_credential': mark_inactive_older_credential(service, user_name)
    }

    response = functions[request_type]
    return response
