import web3 as web3
import time


def send_transaction(web3_connector, function_call, private_key):
    address = web3.Account.from_key(private_key).address
    transaction = function_call.build_transaction({"from": address})
    transaction['nonce'] = web3_connector.eth.get_transaction_count(address)
    signed_tx = web3_connector.eth.account.sign_transaction(transaction, private_key=private_key)
    print("Transaction signed: {}".format(signed_tx))
    hash_tx = web3_connector.eth.send_raw_transaction(signed_tx.rawTransaction).hex()
    print("Transaction sent hash: {}".format(hash_tx))
    __wait_till_transaction_minted(web3_connector, hash_tx)
    return hash_tx


def __wait_till_transaction_minted(web3_connector, tx_hash):
    while True:
        status = web3_connector.eth.get_transaction(tx_hash)
        time.sleep(1)
        if status['blockNumber'] is not None and status['blockNumber'] != 0:
            print("Transaction minted: {}".format(tx_hash))
            return status
        print("Transaction minting: {}...".format(tx_hash))
        time.sleep(2)
