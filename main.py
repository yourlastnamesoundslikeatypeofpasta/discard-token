import logging
import hashlib
import json

from flask import Flask
from flask import request
from flask import jsonify
from flask import render_template
from flask_restful import reqparse, abort, Api, Resource

from discard_token import DiscardToken
from p2p import PeerNode

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
api = Api(app)

blockchain = DiscardToken()
node = PeerNode(blockchain)


class Chain(Resource):

    # get blockchain
    @staticmethod
    def get():
        chain = blockchain.get_chain()
        return chain, 200

    # add transaction and block to blockchain
    def post(self):
        tx_data = request.get_json(force=True)
        is_transaction_added = blockchain.add_transaction(tx_data)
        if is_transaction_added.get('status'):
            node.broadcast_transaction(tx_data)

        # add block to chain
        if is_transaction_added.get('status'):
            is_block_mined = blockchain.mine()
            if is_block_mined.get('status'):
                node.broadcast_block(is_block_mined['block'])
                return is_block_mined, 201
            else:
                return is_block_mined, 404
        else:
            return is_transaction_added, 404


class TxLargest(Resource):

    @staticmethod
    def get():
        largest_transaction = {'largest_transaction': blockchain.get_largest_transaction_amount()}
        return largest_transaction, 200


class TxAverage(Resource):

    @staticmethod
    def get():
        average_transaction = {'average_transaction': blockchain.get_average_transaction_amount()}
        return average_transaction, 200


class ChainTotalTokens(Resource):

    @staticmethod
    def get():
        total_tokens = {'total_tokens': blockchain.get_total_tokens()}
        return total_tokens, 200


class ChainTotalBlocks(Resource):

    @staticmethod
    def get():
        total_blocks = {'total_blocks': blockchain.get_last_index()}
        return total_blocks, 200


class Block(Resource):

    @staticmethod
    def abort_if_block_doesnt_exist(block_index):
        if block_index == 0:
            return

        num_blocks = blockchain.get_last_index() + 1
        if block_index not in range(num_blocks):
            abort(404, error_code='block_doesnt_exist', error=f"Block {block_index} doesn't exist")

    def get(self, block_index):
        self.abort_if_block_doesnt_exist(block_index)
        return blockchain.get_chain()[block_index], 200


class Address(Resource):

    @staticmethod
    def get():
        address_lst = blockchain.get_all_addresses()
        return address_lst, 200


class AddressBalance(Resource):
    @staticmethod
    def abort_if_address_doesnt_exist(address):
        address_lst = blockchain.get_all_addresses()['address_lst']
        if address not in address_lst:
            abort(404, error_code='address_doesnt_exist', error=f"Wallet Address: {address} doesn't exist")

    def get(self, address):
        self.abort_if_address_doesnt_exist(address)
        balance_data = blockchain.get_wallet_balance(address)
        return balance_data, 200


class CreateWallet(Resource):

    @staticmethod
    def get():
        wallet = blockchain.create_wallet()
        return wallet, 200


class Tx(Resource):
    @staticmethod
    def abort_if_tx_hash_doesnt_exist(tx_hash):
        transaction = blockchain.get_tx(tx_hash)
        if not transaction:
            abort(404, error_code='transaction_doesnt_exist', error=f"Transaction Hash: {tx_hash} doesn't exist")

    def get(self, tx_hash):
        transaction = blockchain.get_tx(tx_hash)
        self.abort_if_tx_hash_doesnt_exist(tx_hash)
        return {"transaction": transaction}, 200


class ChainLastBlock(Resource):

    @staticmethod
    def get():
        last_block = blockchain.get_chain()[-1]
        return last_block, 200


class ChainValid(Resource):

    @staticmethod
    def get():
        return {'is_valid': blockchain.is_chain_valid()}, 200


class ChainLastHash(Resource):

    @staticmethod
    def get():
        return {'last_hash': blockchain.get_last_block_hash()}, 200


class ChainTotalTransactions(Resource):

    @staticmethod
    def get():
        total_transactions = sum(len(block['transactions']) for block in blockchain.get_chain())
        return {'total_transactions': total_transactions}, 200


class PendingTransactions(Resource):

    @staticmethod
    def get():
        return {'pending_transactions': blockchain.get_pending_transactions()}, 200


class Mine(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('miner_address', type=str)

    def get(self):
        args = self.parser.parse_args()
        miner_address = args.get('miner_address')
        result = blockchain.mine(miner_address)
        if result.get('status'):
            node.broadcast_block(result['block'])
            return result, 201
        return result, 404


class BlockHash(Resource):

    @staticmethod
    def get(block_index):
        Block.abort_if_block_doesnt_exist(block_index)
        block = blockchain.get_chain()[block_index]
        return {'block_hash': blockchain.get_block_hash(block)}, 200


class DetermineWinner(Resource):

    @staticmethod
    def get():
        winner = blockchain.determine_winner()
        return {'winner': winner}, 200


class RegisterPeer(Resource):

    def post(self):
        data = request.get_json(force=True)
        url = data.get('url')
        pub = data.get('public_key')
        if not url or not pub:
            abort(400, error_code='invalid', error='url and public_key required')
        node.add_peer(url, pub)
        return {'status': True, 'node_id': node.node_id}, 201


class PeerTransaction(Resource):

    def post(self):
        data = request.get_json(force=True)
        tx = data.get('transaction')
        sig = data.get('signature')
        pub = data.get('public_key')
        peer_id = data.get('node_id')
        if not all([tx, sig, pub, peer_id]):
            abort(400, error_code='invalid', error='missing data')
        if peer_id != hashlib.sha256(pub.encode()).hexdigest():
            return {'status': False, 'error': 'Invalid identity'}, 400
        if not PeerNode.verify(tx, pub, sig):
            return {'status': False, 'error': 'Invalid signature'}, 400
        res = blockchain.add_transaction(tx)
        if res.get('status'):
            node.broadcast_transaction(tx)
            return res, 201
        return res, 400


class PeerBlock(Resource):

    def post(self):
        data = request.get_json(force=True)
        block = data.get('block')
        sig = data.get('signature')
        pub = data.get('public_key')
        peer_id = data.get('node_id')
        if not all([block, sig, pub, peer_id]):
            abort(400, error_code='invalid', error='missing data')
        if peer_id != hashlib.sha256(pub.encode()).hexdigest():
            return {'status': False, 'error': 'Invalid identity'}, 400
        if not PeerNode.verify(block, pub, sig):
            return {'status': False, 'error': 'Invalid signature'}, 400
        added = blockchain.add_block(block)
        if added and blockchain.is_chain_valid():
            node.broadcast_block(block)
            return {'status': True}, 201
        return {'status': False}, 400


# ----- Simple HTML Frontend Routes -----
@app.route('/')
def index():
    total_blocks = blockchain.get_last_index() + 1
    return render_template('index.html', total_blocks=total_blocks)


@app.route('/chain/view')
def chain_page():
    chain_json = json.dumps(blockchain.get_chain(), indent=2)
    return render_template('chain.html', chain_json=chain_json)


@app.route('/wallet/create')
def create_wallet_page():
    wallet = blockchain.create_wallet()
    return render_template('create_wallet.html', wallet=wallet)


api.add_resource(Chain, '/chain')
api.add_resource(ChainTotalTokens, '/chain/total-tokens')
api.add_resource(ChainTotalBlocks, '/chain/total-blocks')
api.add_resource(Block, '/chain/block/<int:block_index>')
api.add_resource(Address, '/all-addresses')
api.add_resource(AddressBalance, '/address/<string:address>')
api.add_resource(CreateWallet, '/address/create')
api.add_resource(Tx, '/tx/<string:tx_hash>')
api.add_resource(TxLargest, '/tx/largest-transaction')
api.add_resource(TxAverage, '/tx/average-transaction')
api.add_resource(ChainLastBlock, '/chain/last-block')
api.add_resource(ChainValid, '/chain/valid')
api.add_resource(ChainLastHash, '/chain/last-hash')
api.add_resource(ChainTotalTransactions, '/chain/total-transactions')
api.add_resource(PendingTransactions, '/pending-transactions')
api.add_resource(Mine, '/mine')
api.add_resource(BlockHash, '/chain/block/<int:block_index>/hash')
api.add_resource(DetermineWinner, '/determine-winner')
api.add_resource(RegisterPeer, '/register-peer')
api.add_resource(PeerTransaction, '/p2p/transaction')
api.add_resource(PeerBlock, '/p2p/block')

if __name__ == '__main__':
    app.run(debug=True)
