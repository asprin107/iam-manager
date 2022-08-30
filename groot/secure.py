import boto3
import botocore.client


class Secure:
    session: boto3.Session
    client: botocore.client

    def __init__(self, session: boto3.session):
        self.client = session.client('kms')

    def encrypt(self, plain_txt: str, key_id: str):
        return self.client.encryt(
            KeyId=key_id,
            Plaintext=plain_txt
        )['CiphertextBlob']

    def decrypt(self, cipher_txt: bytes, key_id: str):
        return self.client.decrypt(
            KeyId=key_id,
            CiphertextBlob=cipher_txt
        )['Plaintext'].decode()
