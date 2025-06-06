import os,sys; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sdk import SDKChain
from discard_token import DiscardToken
import pytest


def test_save_and_load_wallet(tmp_path):
    wallet = DiscardToken.create_wallet()
    file_path = tmp_path / "wallet.dat"
    SDKChain.save_wallet(wallet, file_path, "secret")
    loaded = SDKChain.load_wallet(file_path, "secret")
    assert wallet == loaded


def test_load_wallet_wrong_password(tmp_path):
    wallet = DiscardToken.create_wallet()
    file_path = tmp_path / "wallet.dat"
    SDKChain.save_wallet(wallet, file_path, "secret")
    with pytest.raises(Exception):
        SDKChain.load_wallet(file_path, "wrong")

