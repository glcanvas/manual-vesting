import json
import sys
import time
import argparse
import os

import web3 as web3
from web3.middleware import geth_poa_middleware

from dataclasses import dataclass

import utils

# 2**256-1
UINT_256_MAX = 115792089237316195423570985008687907853269984665640564039457584007913129639935

folder_path = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(folder_path, "abi", "Vesting.json"), "r") as f:
    vesting_abi = json.load(f)
with open(os.path.join(folder_path, "abi", "ERC20.json"), "r") as f:
    erc_20_abi = json.load(f)


@dataclass
class ConfigHolder:
    provider: web3.Web3
    private_key: str
    vesting: str
    tokens: list
    recipients: list


def extract_config(path_to_config, fail_on_error, latest_config=None) -> ConfigHolder:
    try:
        with open(path_to_config, "r") as f:
            config = json.load(f)
        web3.Account.from_key(config['private_key'])
        provider = web3.Web3(web3.HTTPProvider(config['provider']))
        provider.middleware_onion.inject(geth_poa_middleware, layer=0)
        vesting = web3.Web3.to_checksum_address(config['vesting'])
        provider.eth.get_balance(vesting)
        tokens = [web3.Web3.to_checksum_address(t) for t in config['tokens']]
        recipients = [(web3.Web3.to_checksum_address(r['address']), float(r['amount'])) for r in config['recipients']]
        total_pct = sum(map(lambda x: x[1], recipients))
        if total_pct > 100.0:
            raise Exception("recipients % > 100: " + total_pct)
        return ConfigHolder(provider,
                            config['private_key'],
                            vesting,
                            tokens,
                            recipients
                            )

    except Exception as e:
        print("Exception happened", e)
        if fail_on_error:
            print("Fail on invalid config")
            raise e
        if latest_config is None:
            print("Initial config invalid, fail")
            raise e
        return latest_config


def give_inf_approve(provider: web3.Web3, private_key: str, vesting: str, token: str):
    owner = web3.Account.from_key(private_key).address
    erc20 = provider.eth.contract(address=token, abi=erc_20_abi)
    balance = erc20.functions.balanceOf(owner).call({"from": owner})
    if balance == 0:
        return
    allowance = erc20.functions.allowance(owner, vesting)
    allowance_balance = allowance.call({"from": owner})
    if allowance_balance >= balance:
        return
    if allowance_balance != 0:
        print("Send Zero approve")
        utils.send_transaction(provider, erc20.functions.approve(owner, vesting, 0), private_key)
    print("Send Max approve")
    utils.send_transaction(provider, erc20.functions.approve(vesting, UINT_256_MAX), private_key)


def do_work_for_token(provider: web3.Web3, private_key: str, vesting: str, token: str, recipients: list):
    owner = web3.Account.from_key(private_key).address
    erc20 = provider.eth.contract(address=token, abi=erc_20_abi)
    balance = erc20.functions.balanceOf(owner).call({"from": owner})
    if balance == 0:
        print("Nothing to send for token: {}, balance: {} = 0".format(token, owner))
        return
    give_inf_approve(provider, private_key, vesting, token)
    tokens_to_send = [(r_a, int(balance * r_p / 100), r_p) for r_a, r_p in recipients]
    tokens_to_send = list(filter(lambda x: x[1] != 0, tokens_to_send))
    if len(tokens_to_send) == 0:
        print("Nothing to send for token: {}, empty recipients".format(token))
        return
    print("Distribution")
    for a, b, p in tokens_to_send:
        print("{} -> {}, {}%".format(a, b, p))

    vesting_contract = provider.eth.contract(address=vesting, abi=vesting_abi)
    f = vesting_contract.functions.distributeRewards(token,
                                                     [i for i, _, _ in tokens_to_send],
                                                     [i for _, i, _ in tokens_to_send])
    utils.send_transaction(provider, f, private_key)
    print("Distributed for token: {}".format(token))


def do_work(config_path, fail_on_error, h: ConfigHolder):
    while True:
        print("Start do work...")
        for t in h.tokens:
            do_work_for_token(h.provider, h.private_key, h.vesting, t, h.recipients)
        h = extract_config(config_path, fail_on_error, h)
        print("Processed all tokens, wait 10 seconds")
        time.sleep(10)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path-to-config")
    parser.add_argument("-f", "--fail-on-error", action=argparse.BooleanOptionalAction)
    parser.parse_args()

    params = parser.parse_args()
    h = extract_config(params.path_to_config, params.fail_on_error, None)
    do_work(params.path_to_config, params.fail_on_error, h)
