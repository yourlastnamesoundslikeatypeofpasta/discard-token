import os
import json
import hashlib
from typing import Dict

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature


class PeerNode:
    """Simple peer node for block and transaction propagation."""

    def __init__(self, blockchain, key_file: str | None = 'node_private.pem', peers_file: str | None = 'peers.json'):
        self.blockchain = blockchain
        self.key_file = key_file
        self.peers_file = peers_file
        self._load_or_create_keys()
        self.peers: Dict[str, Dict[str, str]] = {}
        if self.peers_file and os.path.exists(self.peers_file):
            try:
                with open(self.peers_file, 'r') as f:
                    self.peers = json.load(f)
            except (IOError, json.JSONDecodeError):
                self.peers = {}

    def _load_or_create_keys(self):
        if self.key_file and os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                self.private_key = serialization.load_pem_private_key(f.read(), password=None)
        else:
            self.private_key = ec.generate_private_key(ec.SECP256K1())
            if self.key_file:
                with open(self.key_file, 'wb') as f:
                    f.write(
                        self.private_key.private_bytes(
                            serialization.Encoding.PEM,
                            serialization.PrivateFormat.PKCS8,
                            serialization.NoEncryption(),
                        )
                    )
        self.public_key = self.private_key.public_key()
        self.public_key_pem = self.public_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()
        self.node_id = hashlib.sha256(self.public_key_pem.encode()).hexdigest()

    def _save_peers(self):
        if self.peers_file:
            try:
                with open(self.peers_file, 'w') as f:
                    json.dump(self.peers, f)
            except IOError:
                pass

    def add_peer(self, url: str, public_key: str) -> None:
        peer_id = hashlib.sha256(public_key.encode()).hexdigest()
        self.peers[peer_id] = {'url': url.rstrip('/'), 'public_key': public_key}
        self._save_peers()

    def sign(self, data) -> str:
        payload = json.dumps(data, sort_keys=True).encode()
        signature = self.private_key.sign(payload, ec.ECDSA(hashes.SHA256()))
        return signature.hex()

    @staticmethod
    def verify(data, public_key_pem: str, signature_hex: str) -> bool:
        public_key = serialization.load_pem_public_key(public_key_pem.encode())
        try:
            public_key.verify(
                bytes.fromhex(signature_hex),
                json.dumps(data, sort_keys=True).encode(),
                ec.ECDSA(hashes.SHA256()),
            )
            return True
        except InvalidSignature:
            return False

    def _broadcast(self, endpoint: str, message: dict) -> None:
        for peer in list(self.peers.values()):
            url = peer['url'] + endpoint
            try:
                requests.post(url, json=message, timeout=3)
            except requests.RequestException:
                continue

    def broadcast_transaction(self, transaction: dict) -> None:
        msg = {
            'transaction': transaction,
            'node_id': self.node_id,
            'public_key': self.public_key_pem,
            'signature': self.sign(transaction),
        }
        self._broadcast('/p2p/transaction', msg)

    def broadcast_block(self, block: dict) -> None:
        msg = {
            'block': block,
            'node_id': self.node_id,
            'public_key': self.public_key_pem,
            'signature': self.sign(block),
        }
        self._broadcast('/p2p/block', msg)

