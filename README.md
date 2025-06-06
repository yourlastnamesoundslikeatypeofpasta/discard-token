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

## Peer Networking

Each node generates its own key pair and signs messages when broadcasting
transactions or blocks. Peers must register with one another using
`POST /register-peer` and provide their public key. Signed data is verified
on receipt before being added to the chain.

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
* `POST /register-peer` – register another node's URL and public key
* `POST /p2p/transaction` – receive a signed transaction from a peer
* `POST /p2p/block` – receive a signed block from a peer

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

## Roadmap

The following high-level roadmap outlines potential directions for extending the
project:

1. **Environment & Testing**
   - Install dependencies from `requirements.txt`.
   - Run the test suite in `tests/` and extend it to cover networking and SDK
     behavior.

2. **Persistence Improvements**
   - Replace the JSON-based `chain_data.json` with a lightweight database such
     as SQLite.
   - Provide serialization and migration tools for backward compatibility.

3. **Peer Networking Enhancements**
   - Implement peer discovery and automatic reconnect logic in `p2p.py`.
   - Add authentication or whitelisting so nodes can control which peers may
     connect.

4. **API and SDK Expansion**
   - Document all endpoints in detail and consider API versioning.
   - Extend `sdk.py` with helpers for wallet management and peer registration,
     and offer a CLI or web interface for interacting with the chain.

5. **Consensus & Security**
   - Evaluate alternative consensus mechanisms or refine proof-of-work
     difficulty adjustments.
   - Enhance transaction validation and add rate limiting to reduce spam.

6. **Deployment and Monitoring**
   - Provide Docker or similar containerization scripts for easier deployment.
   - Add logging, metrics and dashboards to monitor node health and
     performance.


## License

This project is provided for educational purposes.
