# Discard Token

Discard Token is a simple blockchain demo implemented in Python. The project exposes a REST API with Flask and includes a small SDK for interacting with the running service.

## Requirements

* Python 3
* `pip` for installing dependencies

Install required packages with:

```bash
pip install -r requirements.txt
```

## Running the API

Start the Flask application by running:

```bash
python main.py
```

The server will listen on `http://127.0.0.1:5000/`.

Each transaction now includes a `transaction_hash` field that uniquely
identifies it on the chain. Transactions are signed using the sender's
private key. Wallet addresses are derived from the SHA256 hash of the
public key.

The blockchain state is stored in `chain_data.json` in the project
directory so that the chain and the mempool of pending transactions
survive server restarts.

Balances include pending outgoing transfers so double spends cannot be
submitted before mining completes.

Transactions require a small fee (default `1` token) which is paid to the
miner of the block. The fee amount is recorded in the `fee` field of each
transaction and is included in the signature payload. Duplicate transactions
or those with non-positive amounts will be rejected before entering the
mempool.

The mining difficulty automatically adjusts after each block to target
approximately one second per block. The difficulty will never fall below
1 or rise above 6.

## Available Endpoints

* `GET /chain` – retrieve the entire blockchain
* `POST /chain` – add a new transaction and mine a block
* `GET /chain/total-tokens` – total amount of tokens that exist
* `GET /chain/total-blocks` – number of blocks in the chain
* `GET /chain/block/<index>` – fetch a block by index
* `GET /all-addresses` – list every known wallet address
* `GET /address/<address>` – view balance details for an address
* `GET /address/create` – generate a new wallet with keys
* `GET /tx/<hash>` – fetch a transaction by its hash
* `GET /tx/largest-transaction` – highest value transaction
* `GET /tx/average-transaction` – average transaction value
* `GET /pending-transactions` – list unmined transactions

## SDK Usage

The `sdk.py` module contains a simple `SDKChain` class for interacting with the service. You can use it to query the chain or post transactions programmatically.

```python
from sdk import SDKChain

client = SDKChain('chain')
response = client.get_chain()
print(response)

# Creating and posting a signed transaction
wallet = client.create_wallet()  # GET /address/create
tx = SDKChain.create_transaction(wallet['private_key'], wallet['address'], 'some_recipient', 10)
client.post_transaction(tx)

# Save the wallet encrypted on disk
SDKChain.save_wallet(wallet, 'wallet.dat', 'my-password')
# Later we can load it again
wallet = SDKChain.load_wallet('wallet.dat', 'my-password')
```

## License

This project is provided for educational purposes.
