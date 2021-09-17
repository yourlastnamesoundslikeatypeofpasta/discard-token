import logging

from flask import Flask
from flask import request
from flask import jsonify
from flask_restful import reqparse, abort, Api, Resource

from discard_token import DiscardToken

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
api = Api(app)

blockchain = DiscardToken()


class Chain(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('sender', type=str)
    parser.add_argument('recipient', type=str)
    parser.add_argument('amount', type=int)

    # get blockchain
    @staticmethod
    def get():
        chain = blockchain.get_chain()
        return chain, 200

    # add transaction and block to blockchain
    def post(self):
        # get args
        args = self.parser.parse_args()
        sender = args.get('sender')
        recipient = args.get('recipient')
        amount = args.get('amount')

        # add transaction to block
        is_transaction_added = blockchain.add_transaction(
            sender,
            recipient,
            amount)

        # add block to chain
        if is_transaction_added.get('status'):
            is_block_mined = blockchain.mine()
            if is_block_mined.get('status'):
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
        wallet_address = blockchain.create_wallet()
        return {"wallet_address": wallet_address}, 200


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

if __name__ == '__main__':
    app.run(debug=True)
