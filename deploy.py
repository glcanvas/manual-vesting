import argparse
import json
import os

import web3 as web3
from web3.middleware import geth_poa_middleware
from loguru import logger

import utils

folder_path = os.path.dirname(os.path.realpath(__file__))


def deploy_contract(path_to_bytecode, path_to_abi, private_key):
    with open(path_to_bytecode, "r") as f:
        bytecode = f.readline()

    with open(path_to_abi, "r") as f:
        abi = json.load(f)

    ctrct = provider.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash = utils.send_transaction(provider, ctrct.constructor(), private_key)
    contract_address = provider.eth.get_transaction_receipt(tx_hash).contractAddress
    return contract_address


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--vesting", action=argparse.BooleanOptionalAction)
    parser.add_argument("--test", action=argparse.BooleanOptionalAction)
    params = parser.parse_args()
    with open('./configs.json', "r") as f:
        config = json.load(f)

    current_chain_name = config['current_chain_name']
    providers = config['providers']
    provider_url = providers.get(current_chain_name, None)
    provider = web3.Web3(web3.HTTPProvider(provider_url))
    provider.middleware_onion.inject(geth_poa_middleware, layer=0)

    pk = config['private_key']
    account_address = web3.Account.from_key(pk).address
    if params.vesting:
        address = deploy_contract(
            os.path.join(folder_path, "bytecode", "Vesting"),
            os.path.join(folder_path, "abi", "Vesting.json"),
            pk
        )
        logger.success(f"Vesting deployed to: {address}, owner: {account_address}")

    if params.test:
        address = deploy_contract(
            os.path.join(folder_path, "bytecode", "TestERC20"),
            os.path.join(folder_path, "abi", "ERC20.json"),
            pk
        )
        logger.success(f"Test ERC20 deployed to: {address}, owner: {account_address}")
