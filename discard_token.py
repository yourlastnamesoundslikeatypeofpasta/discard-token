import os
import random
import hashlib
import json
import time
from statistics import mean, median
import string

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature


class DiscardToken:
    def __init__(self, storage_file='chain_data.json'):
        self.tx_fee = 1
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
                    fee=0
                )
            ],
            'previous_hash': self.genesis_hash,
        }
        self.difficulty = 4
        self.max_difficulty = 6
        self.target_block_time = 1.0
        self.mining_reward = 50
        self.genesis_block['nonce'] = 0
        self.genesis_block['hash'] = self.get_block_hash(self.genesis_block)
        self.chain = [self.genesis_block]
        self.current_trans = []
        self.storage_file = storage_file
        self._load_state()
        self._save_state()

    def _load_state(self):
        """Load chain and pending transactions from disk if available."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    self.chain = data.get('chain', self.chain)
                    self.current_trans = data.get('pending', self.current_trans)
                    self.difficulty = data.get('difficulty', self.difficulty)
            except (IOError, json.JSONDecodeError):
                pass

    def _save_state(self):
        """Persist chain and pending transactions to disk."""
        data = {
            'chain': self.chain,
            'pending': self.current_trans,
            'difficulty': self.difficulty,
        }
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(data, f)
        except IOError:
            pass

    def create_transaction(self, sender, recipient, amount, private_key_pem=None, fee=None):
        """Create and sign a transaction dict."""
        if fee is None:
            fee = self.tx_fee
        payload = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'fee': fee,
            'timestamp': time.time(),
            'nonce': random.random(),
        }
        tx = payload.copy()
        tx['transaction_hash'] = self.hash_str(payload)

        if private_key_pem:
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode(), password=None
            )
            signature = private_key.sign(
                json.dumps(payload, sort_keys=True).encode(),
                ec.ECDSA(hashes.SHA256()),
            )
            tx['signature'] = signature.hex()
            public_key = private_key.public_key()
            tx['public_key'] = public_key.public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode()
        return tx

    def _verify_transaction(self, transaction):
        required = ['sender', 'recipient', 'amount', 'fee', 'timestamp', 'nonce',
                    'transaction_hash', 'signature', 'public_key']
        if not all(k in transaction for k in required):
            return False

        payload = {
            'sender': transaction['sender'],
            'recipient': transaction['recipient'],
            'amount': transaction['amount'],
            'fee': transaction['fee'],
            'timestamp': transaction['timestamp'],
            'nonce': transaction['nonce'],
        }
        if self.hash_str(payload) != transaction['transaction_hash']:
            return False

        if self.hash_str(transaction['public_key']) != transaction['sender']:
            return False

        public_key = serialization.load_pem_public_key(
            transaction['public_key'].encode())
        try:
            public_key.verify(
                bytes.fromhex(transaction['signature']),
                json.dumps(payload, sort_keys=True).encode(),
                ec.ECDSA(hashes.SHA256()),
            )
            return True
        except InvalidSignature:
            return False

    def add_transaction(self, transaction):
        if not self._verify_transaction(transaction):
            return {'status': False, 'error': 'Invalid Signature'}
        if transaction['amount'] <= 0 or transaction.get('fee', 0) < 0:
            return {'status': False, 'error': 'Invalid Amount'}
        if self.get_tx(transaction['transaction_hash']):
            return {'status': False, 'error': 'Duplicate Transaction'}
        sender = transaction['sender']
        amount = transaction['amount']
        fee = transaction.get('fee', self.tx_fee)
        sender_balance = self.get_wallet_balance(sender).get('balance')
        pending_outgoing = self.get_pending_outgoing_total(sender)
        available_balance = sender_balance - pending_outgoing
        if available_balance > amount + fee:
            self.current_trans.append(transaction)
            self._save_state()
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
        self._save_state()
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

    def get_pending_outgoing_total(self, address):
        """Total amount of tokens this address has in pending outgoing tx."""
        total = 0
        for tx in self.current_trans:
            if tx.get('sender') == address:
                total += tx.get('amount', 0)
        return total

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
                    amount_sent += transaction['amount'] + transaction.get('fee', 0)
                    transactions += 1

        # find difference
        wallet_balance = amount_received - amount_sent
        pending_outgoing = self.get_pending_outgoing_total(address)
        return {
            'amount_received': amount_received,
            'amount_sent': amount_sent,
            'transactions': transactions,
            'balance': wallet_balance,
            'pending_outgoing': pending_outgoing,
        }

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

    def get_median_transaction_amount(self):
        """Return the median value of all transactions on the chain."""
        amounts = self.get_transaction_amount_lst()
        if not amounts:
            return 0
        return median(amounts)

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
        issuance_transaction = self.create_transaction('', address, reward, fee=0)
        self.current_trans.append(issuance_transaction)
        self._save_state()

    def proof_of_work(self, block):
        block['nonce'] = 0
        block_hash = self.get_block_hash(block)
        while not block_hash.startswith('0' * self.difficulty):
            block['nonce'] += 1
            block_hash = self.get_block_hash(block)
        return block_hash

    def adjust_difficulty(self, elapsed):
        if elapsed < self.target_block_time * 0.5 and self.difficulty < self.max_difficulty:
            self.difficulty += 1
        elif elapsed > self.target_block_time * 1.5 and self.difficulty > 1:
            self.difficulty -= 1
        self._save_state()

    def mine(self, miner_address=None):
        total_fees = sum(tx.get('fee', 0) for tx in self.current_trans)
        if miner_address:
            self.issue_newly_generated_coins(miner_address, self.mining_reward + total_fees)
        if not self.current_trans:
            return {'status': False, 'error': 'No transactions to mine'}
        start_time = time.time()
        block = {
            'index': self.get_last_index() + 1,
            'timestamp': start_time,
            'transactions': self.current_trans.copy(),
            'previous_hash': self.get_last_block_hash(),
            'nonce': 0
        }
        block_hash = self.proof_of_work(block)
        block['hash'] = block_hash
        self.current_trans = []
        added = self.add_block(block)
        end_time = time.time()
        if added and self.is_chain_valid():
            self.adjust_difficulty(end_time - start_time)
            return {'status': True, 'block': block}
        return {'status': False, 'block': block}

    @staticmethod
    def create_wallet():
        """Generate an ECDSA key pair and return wallet details."""
        private_key = ec.generate_private_key(ec.SECP256K1())
        priv_pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode()
        public_key = private_key.public_key()
        pub_pem = public_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()
        address = DiscardToken.hash_str(pub_pem)
        return {
            'private_key': priv_pem,
            'public_key': pub_pem,
            'address': address,
        }

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



