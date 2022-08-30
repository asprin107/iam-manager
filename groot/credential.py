from datetime import datetime

import boto3
import botocore.client
from enum import Enum
import date_format


class Status(Enum):
    Active = 'Active'
    Inactive = 'Inactive'


class Credential:
    session: boto3.Session
    client: botocore.client
    df = date_format.basic

    def __init__(self, session: boto3.Session):
        self.client = session.client('iam')

    def create(self, user_name: str):
        """
        Publish a new Credential for IAM User. After creation, Remove older credential.

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
        print(f"[{datetime.now().strftime(self.df)}] CREATE a new credential started. User : {user_name}")
        access_key = self.client.create_access_key(UserName=user_name)
        print(f"[{datetime.now().strftime(self.df)}] CREATE a new credential done. User : {user_name}, AccessKeyId : {access_key['AccessKey']['AccessKeyId']}")
        return access_key

    def delete(self, user_name: str, access_key_id: str):
        """
        Delete credential.

        :param user_name: IAM User name
        :param access_key_id: Access key id related to iam user.
        :return: None
        """
        print(f"[{datetime.now().strftime(self.df)}] DELETE Credential started. User : {user_name}, AccessKeyId : {access_key_id}")
        self.client.delete_access_key(
            UserName=user_name,
            AccessKeyId=access_key_id
        )
        print(f"[{datetime.now().strftime(self.df)}] DELETE Credential done. AccessKeyId : {access_key_id} deleted.")

    def change_status(self, user_name: str, access_key_id: str, status: Status):
        """
        Change credential status. (Active or Inactive)

        :param user_name: IAM User name
        :param access_key_id: Access key id related to iam user.
        :param status: Status.Active or Status.Inactive
        :return: bool. True for success False for failed
        """
        print(f"[{datetime.now().strftime(self.df)}] CHANGE credential status as {status} started. User : {user_name},"
              f" AccessKeyId : {access_key_id}")
        try:
            self.client.update_access_key(
                UserName=user_name,
                AccessKeyId=access_key_id,
                Status=status
            )
        except Exception as e:
            print(f"[{datetime.now().strftime(self.df)}] Exception occur during change the credential status: {e}")
            return False
        finally:
            print(
                f"[{datetime.now().strftime(self.df)}] CHANGE credential status as {status} done.")
        return True

    def make_inactive(self, user_name: str, access_key_id: str):
        """
        Change credential status as Inactive.

        :param user_name: IAM User name
        :param access_key_id: Access key id related to iam user.
        :return: bool. True for success False for failed
        """
        return self.change_status(user_name=user_name, access_key_id=access_key_id, status=Status.Inactive)

    def make_active(self, user_name: str, access_key_id: str):
        """
        Change credential status as Active.

        :param user_name: IAM User name
        :param access_key_id: Access key id related to iam user.
        :return: bool. True for success False for failed
        """
        return self.change_status(user_name=user_name, access_key_id=access_key_id, status=Status.Active)

    def list(self, user_name: str):
        """
        List credentials related to IAM User.
        :param user_name: IAM User name
        :return:
        {
            'AccessKeyMetadata': [
                {
                    'UserName': 'string',
                    'AccessKeyId': 'string',
                    'Status': 'Active'|'Inactive',
                    'CreateDate': datetime(2015, 1, 1)
                },
            ],
            'IsTruncated': True|False,
            'Marker': 'string'
        }
        """
        print(f"[{datetime.now().strftime(self.df)}] LIST credentials for User : {user_name}")
        return self.client.list_access_key(UserName=user_name)
