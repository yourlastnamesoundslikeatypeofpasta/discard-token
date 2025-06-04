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
                self.create_transaction(
                    "GENESIS COIN BASE",
                    "the_kings_wallet",
                    self.genesis_tokens,
                )
            ],
            'previous_hash': self.genesis_hash,
        }
        self.difficulty = 4
        self.mining_reward = 50
        self.genesis_block['nonce'] = 0
        self.genesis_block['hash'] = self.get_block_hash(self.genesis_block)
        self.chain = [self.genesis_block]
        self.current_trans = []

    def create_transaction(self, sender, recipient, amount):
        """Create a transaction dict with a unique transaction hash."""
        tx = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        }
        # Include timestamp and random value so hash is unique
        tx['transaction_hash'] = self.hash_str({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'time': time.time(),
            'nonce': random.random(),
        })
        return tx

    def add_transaction(self, sender, recipient, amount):
        transaction = self.create_transaction(sender, recipient, amount)
        sender_balance = self.get_wallet_balance(sender).get('balance')
        if sender_balance > amount:
            self.current_trans.append(transaction)
            return {'status': True, 'transaction': transaction}
        return {'status': False, 'error': 'Insufficient Balance'}

    def add_block(self, block):
        """Add a mined block to the chain after validation."""
        previous_hash = self.get_last_block_hash()
        if block['previous_hash'] != previous_hash:
            return False
        block_hash = self.get_block_hash({k: block[k] for k in block if k != 'hash'})
        if not block_hash.startswith('0' * self.difficulty):
            return False
        if block_hash != block['hash']:
            return False
        self.chain.append(block)
        return True

    def is_chain_valid(self):
        for index in range(1, len(self.chain)):
            current = self.chain[index]
            previous = self.chain[index - 1]
            prev_hash = self.get_block_hash({k: previous[k] for k in previous if k != 'hash'})
            if current['previous_hash'] != prev_hash:
                return False
            calculated_hash = self.get_block_hash({k: current[k] for k in current if k != 'hash'})
            if not calculated_hash.startswith('0' * self.difficulty):
                return False
            if calculated_hash != current['hash']:
                return False
        return True

    def get_last_block_hash(self):
        last_block = self.chain[-1]
        block_contents = {k: last_block[k] for k in last_block if k != 'hash'}
        block_string = json.dumps(block_contents, sort_keys=True).encode()
        previous_block_hash = hashlib.sha256(block_string).hexdigest()
        return previous_block_hash

    def get_chain(self):
        return self.chain

    def get_pending_transactions(self):
        """Return transactions waiting to be mined."""
        return self.current_trans

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
            for transaction in block['transactions']:
                if transaction.get('transaction_hash') == tx_hash:
                    return transaction
        # Also check pending transactions
        for transaction in self.current_trans:
            if transaction.get('transaction_hash') == tx_hash:
                return transaction

    def issue_newly_generated_coins(self, address, reward):
        issuance_transaction = self.create_transaction('', address, reward)
        self.current_trans.append(issuance_transaction)

    def proof_of_work(self, block):
        block['nonce'] = 0
        block_hash = self.get_block_hash(block)
        while not block_hash.startswith('0' * self.difficulty):
            block['nonce'] += 1
            block_hash = self.get_block_hash(block)
        return block_hash

    def mine(self, miner_address=None):
        if miner_address:
            self.issue_newly_generated_coins(miner_address, self.mining_reward)
        if not self.current_trans:
            return {'status': False, 'error': 'No transactions to mine'}
        block = {
            'index': self.get_last_index() + 1,
            'timestamp': time.time(),
            'transactions': self.current_trans.copy(),
            'previous_hash': self.get_last_block_hash(),
            'nonce': 0
        }
        block_hash = self.proof_of_work(block)
        block['hash'] = block_hash
        self.current_trans = []
        added = self.add_block(block)
        if added and self.is_chain_valid():
            return {'status': True, 'block': block}
        return {'status': False, 'block': block}

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

            return None



