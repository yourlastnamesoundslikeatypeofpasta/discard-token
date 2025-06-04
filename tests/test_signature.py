import unittest
from discard_token import DiscardToken

class TestSignature(unittest.TestCase):
    def test_forged_transaction_rejected(self):
        bc = DiscardToken()
        sender = bc.create_wallet()
        recipient = bc.create_wallet()
        bc.mine(sender['address'])  # reward sender so they have balance
        tx = bc.create_transaction(sender['address'], recipient['address'], 5, sender['private_key'])
        res = bc.add_transaction(tx)
        self.assertTrue(res['status'])

        # Forge tx with wrong key
        fake_wallet = bc.create_wallet()
        forged_tx = bc.create_transaction(sender['address'], recipient['address'], 5, fake_wallet['private_key'])
        forged_tx['sender'] = sender['address']
        res2 = bc.add_transaction(forged_tx)
        self.assertFalse(res2['status'])

if __name__ == '__main__':
    unittest.main()
