import os
import random
import string
import json
import time
import hashlib
import base64

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet


class SDKChain:
    chain_path = 'http://127.0.0.1:5000/'

    def __init__(self, rel_chain_path):
        self.chain_rel_path = rel_chain_path
        self.chain_path = os.path.join(self.chain_path, self.chain_rel_path)

    def get_chain(self):
        r_get_chain = requests.get(self.chain_path)
        status = r_get_chain.status_code
        data = r_get_chain.json()
        return {'status': status, 'data': data}

    @staticmethod
    def create_wallet():
        resp = requests.get('http://127.0.0.1:5000/address/create')
        return resp.json()

    @staticmethod
    def _derive_key(password: str, salt: bytes) -> bytes:
        """Derive a symmetric key from the given password and salt."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=390000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    @staticmethod
    def save_wallet(wallet: dict, path: str, password: str) -> None:
        """Encrypt wallet data with password and save to path."""
        salt = os.urandom(16)
        key = SDKChain._derive_key(password, salt)
        f = Fernet(key)
        token = f.encrypt(json.dumps(wallet).encode())
        with open(path, 'wb') as fobj:
            fobj.write(salt + token)

    @staticmethod
    def load_wallet(path: str, password: str) -> dict:
        """Load and decrypt wallet data from path."""
        with open(path, 'rb') as fobj:
            data = fobj.read()
        salt, token = data[:16], data[16:]
        key = SDKChain._derive_key(password, salt)
        f = Fernet(key)
        decrypted = f.decrypt(token)
        return json.loads(decrypted.decode())

    @staticmethod
    def create_transaction(private_key_pem, sender, recipient, amount):
        private_key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)
        payload = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'timestamp': time.time(),
            'nonce': random.random(),
        }
        tx = payload.copy()
        tx['transaction_hash'] = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()
        signature = private_key.sign(
            json.dumps(payload, sort_keys=True).encode(),
            ec.ECDSA(hashes.SHA256()),
        )
        tx['signature'] = signature.hex()
        tx['public_key'] = private_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()
        return tx

    def post_transaction(self, transaction):
        r_post_transaction = requests.post(self.chain_path, json=transaction)
        status = r_post_transaction.status_code
        data = r_post_transaction.json()
        return {'status': status, 'data': data}

    def create_fake_transactions(self, num_transactions):
        for _ in range(num_transactions):
            random_recipient = ''.join(
                random.choices(string.ascii_letters + string.digits, k=32)
            )
            tx = {
                'sender': 'the_kings_wallet',
                'recipient': random_recipient,
                'amount': random.randint(0, num_transactions),
                'timestamp': time.time(),
                'nonce': random.random(),
                'transaction_hash': '',
                'signature': '',
                'public_key': '',
            }
            # Unsigned transactions for fake data
            tx['transaction_hash'] = hashlib.sha256(
                json.dumps({k: tx[k] for k in ['sender','recipient','amount','timestamp','nonce']}, sort_keys=True).encode()
            ).hexdigest()
            self.post_transaction(tx)

    def get_last_block(self):
        url = os.path.join(self.chain_path, 'last-block')
        resp = requests.get(url)
        return {'status': resp.status_code, 'data': resp.json()}

    def get_validity(self):
        url = os.path.join(self.chain_path, 'valid')
        resp = requests.get(url)
        return {'status': resp.status_code, 'data': resp.json()}

    def get_last_hash(self):
        url = os.path.join(self.chain_path, 'last-hash')
        resp = requests.get(url)
        return {'status': resp.status_code, 'data': resp.json()}

    def get_total_transactions(self):
        url = os.path.join(self.chain_path, 'total-transactions')
        resp = requests.get(url)
        return {'status': resp.status_code, 'data': resp.json()}

    def get_pending_transactions(self):
        url = os.path.join('http://127.0.0.1:5000', 'pending-transactions')
        resp = requests.get(url)
        return {'status': resp.status_code, 'data': resp.json()}

    def mine(self, miner_address=None):
        url = os.path.join('http://127.0.0.1:5000', 'mine')
        params = {'miner_address': miner_address} if miner_address else {}
        resp = requests.get(url, params=params)
        return {'status': resp.status_code, 'data': resp.json()}

    def get_block_hash(self, block_index):
        url = os.path.join(self.chain_path, f'block/{block_index}/hash')
        resp = requests.get(url)
        return {'status': resp.status_code, 'data': resp.json()}

    def determine_winner(self):
        url = os.path.join('http://127.0.0.1:5000', 'determine-winner')
        resp = requests.get(url)
        return {'status': resp.status_code, 'data': resp.json()}
