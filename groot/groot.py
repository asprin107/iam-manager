from datetime import datetime, timezone
import boto3
from credential import Credential, Status
from account import Account
import date_format

df = date_format.basic


class Service:
    session: boto3.Session
    credential_handler: Credential
    account_handler: Account

    def __init__(self, access_key_id: str, secret_access_key: str):
        self.set_session_profile(access_key_id=access_key_id, secret_access_key=secret_access_key)

    def set_session_profile(self, access_key_id: str, secret_access_key: str):
        print(f"[{datetime.now().strftime(df)}] SERVICE:SET AWS session profile. AccessKeyId: \'{access_key_id}\'")
        self.session = boto3.session.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key
        )
        self.credential_handler = Credential(session=self.session)
        self.account_handler = Account(session=self.session)

    def publish_new_credential(self, user_name: str):
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
        access_key = self.credential_handler.create(user_name=user_name)
        print(f"[{datetime.now().strftime(df)}] SERVICE:PUBLISH a new credential for User : {user_name}, AccessKeyId : {access_key['AccessKey']['AccessKeyId']}")

        self.mark_inactive_older_credential(user_name=user_name)
        self.set_session_profile(access_key_id=access_key['AccessKey']['AccessKeyId'],
                                 secret_access_key=access_key['AccessKey']['SecretAccessKey'])
        self.remove_inactive_credential(user_name=user_name)
        return access_key

    def delete_credential(self, user_name: str, access_key_id: str):
        """
            Delete credential.

            :param user_name: IAM User name
            :param access_key_id: Access key id related to iam user.
            :return: None
            """
        print(f"[{datetime.now().strftime(df)}] SERVICE:DELETE Credential : {user_name}, AccessKeyId : {access_key_id}")
        self.credential_handler.delete(user_name=user_name, access_key_id=access_key_id)

    def get_account_info(self):
        """
        Get AWS Account information

        :return:
        """
        return self.account_handler.get_aws_account_info()

    def need_to_publish_new_credential(self, user_name: str):
        """
        Check if it need to publish a new credential.

        :param user_name: IAM User name
        :return: bool. True for need to publish a new credential, False for don't need to.
        """
        credentials = self.credential_handler.list(user_name=user_name)['AccessKeyMetadata']
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
            duration = credentials[0]['CreateDate'] - datetime.now(timezone.utc)
            if duration.days >= 75:  # 생성한지 75일 지난 경우 credential 재발행.
                print(f'[{datetime.now().strftime(df)}] REPORT iam user \'{user_name}\' need to publish a new credential.')
                return True
            else:
                print(f'[{datetime.now().strftime(df)}] REPORT iam user \'{user_name}\' don\'t need to publish a new credential.')
                return False
        elif amt_credentials == 2:
            self.mark_inactive_older_credential(user_name=user_name)
            raise Exception("Error, Can't determine which credential is correct.")
        else:
            raise Exception("Error, Maximum credentials related to IAM User is 2.")

    def remove_inactive_credential(self, user_name: str):
        """
        Remove credential that status is inactive.

        :param user_name: IAM User name.
        :return: None
        """
        print(f'[{datetime.now().strftime(df)}] SERVICE:REMOVE Inactive credentials for \'{user_name}\'')
        credentials = self.credential_handler.list(user_name=user_name)['AccessKeyMetadata']
        for credential in credentials:
            if credential['Status'] == Status.Inactive:
                self.credential_handler.delete(user_name=user_name, access_key_id=credential['AccessKeyId'])
            else:
                pass

    def mark_inactive_older_credential(self, user_name: str):
        """
        Compare 2 credentials creation date in a same IAM user. Then make older credential status as Inactive.

        :param user_name: IAM User name.
        :return: None.
        """
        credentials = self.credential_handler.list(user_name=user_name)['AccessKeyMetadata']
        if credentials[0]['CreateDate'] > credentials[1]['CreateDate']:
            inactive_target_access_key = credentials[1]['AccessKeyId']
        else:
            inactive_target_access_key = credentials[0]['AccessKeyId']
        print(f"[{datetime.now().strftime(df)}] SERVICE:MARK credential Inactive. User : {user_name}, "
              f"AccessKeyId : {inactive_target_access_key}")
        self.credential_handler.make_inactive(user_name=user_name, access_key_id=inactive_target_access_key)
