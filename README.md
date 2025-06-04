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

## Available Endpoints

* `GET /chain` – retrieve the entire blockchain
* `POST /chain` – add a new transaction and mine a block
* `GET /chain/total-tokens` – total amount of tokens that exist
* `GET /chain/total-blocks` – number of blocks in the chain
* `GET /chain/block/<index>` – fetch a block by index
* `GET /all-addresses` – list every known wallet address
* `GET /address/<address>` – view balance details for an address
* `GET /address/create` – generate a new wallet address
* `GET /tx/<hash>` – fetch a transaction by its hash
* `GET /tx/largest-transaction` – highest value transaction
* `GET /tx/average-transaction` – average transaction value

## SDK Usage

The `sdk.py` module contains a simple `SDKChain` class for interacting with the service. You can use it to query the chain or post transactions programmatically.

```python
from sdk import SDKChain

client = SDKChain('chain')
response = client.get_chain()
print(response)
```

## License

This project is provided for educational purposes.
