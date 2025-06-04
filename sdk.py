import os
import random
import string

import requests


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

    def post_transaction(self, sender, recipient, amount):
        transaction = {'sender': sender, 'recipient': recipient, 'amount': amount}
        r_post_transaction = requests.post(self.chain_path, data=transaction)
        status = r_post_transaction.status_code
        data = r_post_transaction.json()
        return {'status': status, 'data': data}

    def create_fake_transactions(self, num_transactions):
        for i in range(num_transactions):
            random_recipient = ''.join(random.choices(string.ascii_letters + string.digits, k=random.choice(
                [i for i in range(25, 36)])))  # create 25 char address

            self.post_transaction('the_kings_wallet', random_recipient, random.randint(0, num_transactions))

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
