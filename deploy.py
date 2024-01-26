import json
import sys
import time
import argparse
import os

folder_path = os.path.dirname(os.path.realpath(__file__))

import web3 as web3
from web3.middleware import geth_poa_middleware

from utils import send_transaction


def deploy_contract(path_to_bytecode, path_to_abi, private_key):
    with open(path_to_bytecode, "r") as f:
        bytecode = f.readline()
    with open(path_to_abi, "r") as f:
        abi = json.load(f)
    ctrct = provider.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash = send_transaction(provider, ctrct.constructor(), private_key)
    contract_address = provider.eth.get_transaction_receipt(tx_hash).contractAddress
    return contract_address


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path-to-config")
    parser.add_argument("--vesting", action=argparse.BooleanOptionalAction)
    parser.add_argument("--test", action=argparse.BooleanOptionalAction)
    params = parser.parse_args()
    with open(params.path_to_config, "r") as f:
        config = json.load(f)

    provider = web3.Web3(web3.HTTPProvider(config['provider']))
    provider.middleware_onion.inject(geth_poa_middleware, layer=0)

    pk = config['private_key']
    account_address = web3.Account.from_key(pk).address
    if params.vesting:
        address = deploy_contract(os.path.join(folder_path, "bytecode", "Vesting"),
                                  os.path.join(folder_path, "abi", "Vesting.json"), pk)
        print("Vesting deployed to: {}, owner: {}".format(address, account_address))

    if params.test:
        address = deploy_contract(os.path.join(folder_path, "bytecode", "TestERC20"),
                                  os.path.join(folder_path, "abi", "ERC20.json"), pk)
        print("Test ERC20 deployed to: {}, owner: {}".format(address, account_address))
