import os,sys; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from discard_token import DiscardToken

CHAIN_FILE = 'chain_data.json'

def setup_function(function):
    if os.path.exists(CHAIN_FILE):
        os.remove(CHAIN_FILE)

def test_genesis_block_exists():
    chain = DiscardToken()
    assert len(chain.get_chain()) == 1
    block = chain.get_chain()[0]
    assert block['index'] == 0
    assert block['transactions'][0]['recipient'] == 'the_kings_wallet'

def test_create_transaction_unique_hashes():
    chain = DiscardToken()
    tx1 = chain.create_transaction('a','b',1)
    tx2 = chain.create_transaction('a','b',1)
    assert tx1['transaction_hash'] != tx2['transaction_hash']

def test_add_transaction_insufficient_balance():
    chain = DiscardToken()
    wallet = chain.create_wallet()
    tx = chain.create_transaction(wallet['address'], 'b', 10, wallet['private_key'])
    res = chain.add_transaction(tx)
    assert res['status'] is False
    assert 'Insufficient Balance' in res['error']

def test_add_transaction_and_mine():
    chain = DiscardToken()
    wallet = chain.create_wallet()
    chain.mine(wallet['address'])  # reward wallet so it has balance
    recipient = chain.create_wallet()
    tx = chain.create_transaction(wallet['address'], recipient['address'], 10, wallet['private_key'])
    res = chain.add_transaction(tx)
    assert res['status']
    tx_hash = res['transaction']['transaction_hash']
    assert chain.get_pending_transactions()
    mine_res = chain.mine()
    assert mine_res['status']
    assert len(chain.get_chain()) == 3
    assert not chain.get_pending_transactions()
    mined_tx = chain.get_tx(tx_hash)
    assert mined_tx is not None

def test_chain_invalid_after_tamper():
    chain = DiscardToken()
    wallet = chain.create_wallet()
    chain.mine(wallet['address'])
    tx = chain.create_transaction(wallet['address'], chain.create_wallet()['address'], 5, wallet['private_key'])
    chain.add_transaction(tx)
    chain.mine()
    chain.chain[1]['transactions'][0]['amount'] = 99
    assert chain.is_chain_valid() is False

def test_create_wallet_length():
    wallet = DiscardToken.create_wallet()
    assert len(wallet) == 3

def test_get_tx_pending_and_mined():
    chain = DiscardToken()
    wallet = chain.create_wallet()
    chain.mine(wallet['address'])
    tx = chain.create_transaction(wallet['address'], 'x', 3, wallet['private_key'])
    chain.add_transaction(tx)
    tx_hash = chain.current_trans[0]['transaction_hash']
    assert chain.get_tx(tx_hash) is not None
    chain.mine()
    assert chain.get_tx(tx_hash) is not None


def test_pending_outgoing_reduces_available_balance():
    chain = DiscardToken()
    wallet = chain.create_wallet()
    chain.mine(wallet['address'])
    first_recipient = chain.create_wallet()
    tx1 = chain.create_transaction(wallet['address'], first_recipient['address'], 30, wallet['private_key'])
    res1 = chain.add_transaction(tx1)
    assert res1['status']
    balance = chain.get_wallet_balance(wallet['address'])
    assert balance['pending_outgoing'] == 30
    second_recipient = chain.create_wallet()
    tx2 = chain.create_transaction(wallet['address'], second_recipient['address'], 30, wallet['private_key'])
    res2 = chain.add_transaction(tx2)
    assert res2['status'] is False
