import random
import hashlib
import json
import string
import time
from statistics import mean


class DiscardToken:
    def __init__(self):
        self.genesis_hash = self.hash_str('DISKARDDDD DOLLARRRR TO THE MOONNNNNN!🚀')
        self.genesis_tokens = 99999999999999
        self.genesis_block = {
            'index': 0,
            "timestamp": time.time(),
            'transactions': [
                {
                    'sender': "GENESIS COIN BASE",
                    'recipient': "the_kings_wallet",
                    'amount': self.genesis_tokens,
                }
            ],
            'previous_hash': self.genesis_hash
        }
        self.chain = [self.genesis_block]
        self.current_trans = []

    def add_transaction(self, sender, recipient, amount):
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        }
        sender_balance = self.get_wallet_balance(sender).get('balance')
        if sender_balance > amount:
            self.current_trans.append(transaction)
            return {'status': True, 'transaction': transaction}
        return {'status': False, 'error': 'Insufficient Balance'}

    def add_block(self):
        # self.issue_newly_generated_coins(winner_address, winner_reward)
        block = {
            'index': self.get_last_index() + 1,
            "timestamp": time.time(),
            'transactions': [
            ],
            'previous_hash': self.get_last_block_hash()
        }

        # move current transactions to block transactions lst & add block to chain
        if self.current_trans:
            while self.current_trans:
                transaction = self.current_trans.pop()
                transaction_hash = self.hash_str(transaction)
                block['transaction_hash'] = transaction_hash
                block['transactions'].append(transaction)
            self.chain.append(block)

    def is_chain_valid(self):
        previous_block = None
        for block in self.chain:
            # validate block 1
            if block['index'] == self.chain[0]['index']:
                if block['previous_hash'] == self.genesis_hash:
                    previous_block = block
                    continue

            # validate other blocks
            previous_block_hash = self.get_block_hash(previous_block)
            if previous_block_hash == block['previous_hash']:
                previous_block = block
                continue
            else:
                print(block)
                return False
        return True

    def get_last_block_hash(self):
        last_block = self.chain[-1]
        block_string = json.dumps(last_block, sort_keys=True).encode()
        previous_block_hash = hashlib.sha256(block_string).hexdigest()
        return previous_block_hash

    def get_chain(self):
        return self.chain

    def get_all_addresses(self):
        address_lst = []
        for block in self.chain:
            for transaction in block['transactions']:
                sender = transaction.get('sender')
                rec = transaction.get('recipient')
                if sender not in address_lst:
                    address_lst.append(sender)
                if rec not in address_lst:
                    address_lst.append(rec)
        return {'address_lst': list(set(address_lst))}

    def get_wallet_balance(self, address):
        transactions = 0
        # check how many tokens address has received
        amount_received = 0
        for block in self.chain:
            for transaction in block['transactions']:
                if transaction['recipient'] == address:
                    amount_received += transaction['amount']
                    transactions += 1

        # check how many tokens address has sent
        amount_sent = 0
        for block in self.chain:
            for transaction in block['transactions']:
                if transaction['sender'] == address:
                    amount_sent += transaction['amount']
                    transactions += 1

        # find difference
        wallet_balance = amount_received - amount_sent
        return {'amount_received': amount_received,
                'amount_sent': amount_sent,
                'transactions': transactions,
                'balance': wallet_balance}

    def get_largest_transaction_amount(self):
        transaction_amount_lst = self.get_transaction_amount_lst()
        for block in self.chain:
            for transaction in block['transactions']:
                transaction_amount = transaction['amount']
                if transaction_amount == self.genesis_tokens:
                    continue
                transaction_amount_lst.append(transaction_amount)
        largest_transaction = max(transaction_amount_lst)
        return largest_transaction

    def get_average_transaction_amount(self):
        transaction_amount_lst = self.get_transaction_amount_lst()
        return mean(transaction_amount_lst)

    def get_total_tokens(self):
        # sum all transactions
        transaction_amount_lst = self.get_transaction_amount_lst()
        return sum(transaction_amount_lst)

    def get_transaction_amount_lst(self):
        # create a list of transaction amounts
        transaction_amount_lst = []
        for block in self.chain:
            for transaction in block['transactions']:
                transaction_amount = transaction['amount']
                if transaction_amount == self.genesis_tokens:
                    continue
                transaction_amount_lst.append(transaction_amount)
        return transaction_amount_lst

    def get_last_index(self):
        last_block = self.chain[-1]
        last_block_index = last_block.get('index')
        return last_block_index

    def get_tx(self, tx_hash):
        for block in self.chain:
            if block.get('transaction_hash') == tx_hash:
                transaction = block.get('transactions')[0]
                return transaction

    def issue_newly_generated_coins(self, address, reward):
        issuance_transaction = {
            'sender': '',
            'recipient': address,
            'amount': reward
        }
        self.current_trans.append(issuance_transaction)

    def mine(self):
        self.add_block()
        if self.is_chain_valid():
            return {'status': True, 'block': self.chain[-1]}
        return {'status': False, 'current_trans': self.current_trans, 'chain': self.chain}

    @staticmethod
    def create_wallet():
        wallet_address = ''.join(
            random.choices(string.ascii_letters + string.digits, k=random.choice([i for i in range(25, 36)])))
        return wallet_address

    @staticmethod
    def hash_str(str_to_hash):
        string_to_hash = json.dumps(str_to_hash, sort_keys=True).encode()
        string_hash = hashlib.sha256(string_to_hash).hexdigest()
        return string_hash

    @staticmethod
    def get_block_hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        block_hash = hashlib.sha256(block_string).hexdigest()
        return block_hash

    @staticmethod
    def determine_winner():
        worker_lst = []
        payouts_lst = []
        for i in range(10):
            random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=4))
            random_payout = random.randint(0, 1500)
            worker_lst.append(random_name)
            payouts_lst.append(random_payout)

        highest_payout = max(payouts_lst)

        try:
            winning_worker_index = payouts_lst.index(highest_payout)
            winning_worker = worker_lst[winning_worker_index]
            print(worker_lst)
            print(highest_payout)
            print(payouts_lst)
            print(list(zip(worker_lst, payouts_lst)))
            return winning_worker
        except ValueError:
            print(worker_lst)
            print(highest_payout)
            print(payouts_lst)
