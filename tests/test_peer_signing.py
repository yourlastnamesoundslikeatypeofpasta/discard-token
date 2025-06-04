import os,sys; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from discard_token import DiscardToken
from p2p import PeerNode


def test_peer_sign_and_verify(tmp_path):
    bc = DiscardToken()
    node = PeerNode(bc, key_file=None, peers_file=None)
    data = {"msg": "hello"}
    sig = node.sign(data)
    assert PeerNode.verify(data, node.public_key_pem, sig)
    other = PeerNode(bc, key_file=None, peers_file=None)
    assert not PeerNode.verify(data, other.public_key_pem, sig)

