from datetime import datetime, timezone
import os
import subprocess
import boto3
import botocore.client
import re

profile_name_val = 'iam-manager'
session = boto3.Session(profile_name=profile_name_val)
sts_client = session.client('sts')
iam_client = session.client('iam')
date_format = '%Y-%m-%d %H:%M:%S:%f %Z'
credential_saved_path = './credentials'


def publish_new_credential(client: botocore.client, user_name: str):
    """
    Publish a new Credential for IAM User. After creation, Remove older credential.

    :param client: AWS iam client.
    :param user_name: IAM User name
    :return:
    {
        'AccessKey': {
            'UserName': 'string',
            'AccessKeyId': 'string',
            'Status': 'Active'|'Inactive',
            'SecretAccessKey': 'string',
            'CreateDate': datetime(2015, 1, 1)
        }
    }
    """
    access_key = client.create_access_key(UserName=user_name)
    write_credential_file(user_name=user_name, access_key_id=access_key['AccessKey']['AccessKeyId'], secret_access_key=access_key['AccessKey']['SecretAccessKey'])
    print(f"[{datetime.now().strftime(date_format)}] PUBLISH a new credential for User : {user_name}, AccessKeyId : {access_key['AccessKey']['AccessKeyId']}")

    mark_inactive_older_credential(client=client, user_name=user_name)
    change_aws_configure(access_key_id=access_key['AccessKey']['AccessKeyId'], secret_access_key=access_key['AccessKey']['SecretAccessKey'], profile_name=profile_name_val)
    clear_inactive_credential(client=client, user_name=user_name)
    return access_key


def delete_credential(client: botocore.client, user_name: str, access_key_id: str):
    """
    Delete credential.

    :param client: AWS iam client.
    :param user_name: IAM User name
    :param access_key_id: Access key id related to iam user.
    :return: None
    """
    print(f"[{datetime.now().strftime(date_format)}] DELETE Credential : {user_name}, AccessKeyId : {access_key_id}")
    client.delete_access_key(
        UserName=user_name,
        AccessKeyId=access_key_id
    )


def get_aws_account_info(client: botocore.client):
    """
    Get AWS Account information

    :param client: AWS sts client.
    :return:
    {
        'Account': {AWS_ACCOUNT_ID},
        'UserArn': 'arn:aws:iam::{ACCOUNT_ID}:user/{IAM_USER_NAME}'
        'UserName': '{IAM_USER_NAME}'
    }
    """
    result = {}
    aws_account_info = client.get_caller_identity()
    result['UserArn'] = aws_account_info['Arn']
    user_name = re.sub(r'arn:aws:iam::+[0-9]*:user', '', result['UserArn'])  # Delete 'arn:aws:iam::{ACCOUNT_ID}:user'
    user_name = user_name.split('/')[-1]  # Remove path, get user name only
    result['UserName'] = user_name
    result['Account'] = aws_account_info['Account']
    return result


def need_to_publish_new_credential(client: botocore.client, user_name: str):
    credentials = client.list_access_keys(UserName=user_name)['AccessKeyMetadata']
    amt_credentials = len(credentials)
    # credential amount :
    # 0개 : 불가능, 비정상
    # 1개 : 가능, 만료시간 check
    # 2개 : 가능, 2개의 credential 중 만료시간이 더 임박한 key 를 inactive 처리. (재귀 불가. 어떤 credential 정보를 사용해야 할지 모름. Normal case 아님.)
    # 그 외 : 불가능, credential 은 iam user 당 2개가 limit. (default)
    if amt_credentials == 0:
        raise Exception("Error, IAM user doesn't have any credential. "
                        "It might IAM User name was wrong or All credentials are Inactive.")
    elif amt_credentials == 1:
        duration = credentials[0]['CreateDate']-datetime.now(timezone.utc)
        if duration.days >= 75:  # 생성한지 75일 지난 경우 credential 재발행.
            print(f'[{datetime.now().strftime(date_format)}] REPORT iam user \'{user_name}\' need to publish a new credential.')
            return True
        else:
            print(f'[{datetime.now().strftime(date_format)}] REPORT iam user \'{user_name}\' don\'t need to publish a new credential.')
            return False
    elif amt_credentials == 2:
        mark_inactive_older_credential(client=client, user_name=user_name)
        raise Exception("Error, Can't determine which credential is correct.")
    else:
        raise Exception("Error, Maximum credentials related to IAM User is 2.")


def clear_inactive_credential(client: botocore.client, user_name: str):
    """
    Clear credential that status is inactive

    :param client: AWS IAM client.
    :param user_name: IAM User name.
    :return: None
    """
    print(f'[{datetime.now().strftime(date_format)}] CLEAR Inactive credentials for \'{user_name}\'')
    credentials = client.list_access_keys(UserName=user_name)['AccessKeyMetadata']
    for credential in credentials:
        if credential['Status'] == 'Inactive':
            delete_credential(client=client, user_name=user_name, access_key_id=credential['AccessKeyId'])
        else:
            pass


def mark_inactive_older_credential(client: botocore.client, user_name: str):
    credentials = client.list_access_keys(UserName=user_name)['AccessKeyMetadata']
    inactive_target_access_key = None
    if credentials[0]['CreateDate'] > credentials[1]['CreateDate']:
        inactive_target_access_key = credentials[1]['AccessKeyId']
    else:
        inactive_target_access_key = credentials[0]['AccessKeyId']
    print(f"[{datetime.now().strftime(date_format)}] MARK credential Inactive. User : {user_name}, "
          f"AccessKeyId : {inactive_target_access_key}")
    client.update_access_key(
        UserName=user_name,
        AccessKeyId=inactive_target_access_key,
        Status='Inactive'
    )


def write_credential_file(user_name: str, access_key_id: str, secret_access_key: str, profile_name=profile_name_val):
    if not os.path.exists(credential_saved_path):
        os.makedirs(credential_saved_path)
    with open(f"{credential_saved_path}/credentials-{user_name}-{access_key_id}", 'w', encoding='utf-8') as f:
        f.write(f"[{profile_name}]\n")
        f.write(f"access_key_id = {access_key_id}\n")
        f.write(f"secret_access_key = {secret_access_key}\n")
    print(f"[{datetime.now().strftime(date_format)}] SAVED Credential at \'{credential_saved_path}/credentials-{user_name}-{access_key_id}\'")


def change_aws_configure(access_key_id: str, secret_access_key: str, profile_name=profile_name_val):
    print(f"[{datetime.now().strftime(date_format)}] CHANGE AWS cli configure using \'{access_key_id}\' with profile name : \'{profile_name}\'")
    subprocess.run(["aws", "configure", "set", "aws_access_key_id", access_key_id, f"--profile={profile_name}"])
    subprocess.run(["aws", "configure", "set", "aws_secret_access_key", secret_access_key, f"--profile={profile_name}"])


def report_log_to_server(msg: str):
    pass


def gossip_to_server(server_host: str, server_port: int):
    pass


if __name__ == '__main__':

    account_info = get_aws_account_info(client=sts_client)

    if need_to_publish_new_credential(iam_client, account_info['UserName']):
        publish_new_credential(client=iam_client, user_name=account_info['UserName'])
