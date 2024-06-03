import argparse
import json
import os
import time
from typing import List

import web3 as web3
from loguru import logger
from web3.middleware import geth_poa_middleware

import utils
from excel_parser import parse_excel
from models.config_holder import ConfigHolder
from models.recipient import Recipient

# 2**256-1
UINT_256_MAX = 115792089237316195423570985008687907853269984665640564039457584007913129639935

folder_path = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(folder_path, "abi", "Vesting.json"), "r") as f:
    vesting_abi = json.load(f)
with open(os.path.join(folder_path, "abi", "ERC20.json"), "r") as f:
    erc_20_abi = json.load(f)


def get_config():
    with open('./configs.json', "r") as f:
        return json.load(f)


def extract_config(fail_on_error, token_address, latest_config=None) -> ConfigHolder:
    try:
        config = get_config()
        logger.info("Extracting config data")
        web3.Account.from_key(config['private_key'])
        provider = web3.Web3(web3.HTTPProvider(config['provider']))
        provider.middleware_onion.inject(geth_poa_middleware, layer=0)
        vesting = web3.Web3.to_checksum_address(config['vesting'])
        token = web3.Web3.to_checksum_address(token_address)
        recipients = parse_excel('./data/addresses.xlsx')

        logger.success("Config extracted")

        return ConfigHolder(
            provider,
            config['private_key'],
            vesting,
            token,
            recipients
        )

    except Exception as e:
        logger.error("Exception happened")
        if fail_on_error:
            logger.error("Fail on invalid config")
            raise e
        if latest_config is None:
            logger.error("Initial config invalid, fail")
            raise e
        return latest_config


def give_inf_approve(provider: web3.Web3, private_key: str, vesting: str, token: str):
    logger.info("Start giving aproove...")
    owner = web3.Account.from_key(private_key).address
    erc20 = provider.eth.contract(address=token, abi=erc_20_abi)
    balance = erc20.functions.balanceOf(owner).call({"from": owner})

    if balance == 0:
        return

    allowance = erc20.functions.allowance(owner, vesting)
    allowance_balance = allowance.call({"from": owner})

    if allowance_balance >= balance:
        logger.info("Allowance_balance is more than balance")
        return

    if allowance_balance != 0:
        logger.info("Send Zero approve")
        utils.send_transaction(provider, erc20.functions.approve(owner, vesting, 0), private_key)

    logger.info("Send Max approve")
    utils.send_transaction(provider, erc20.functions.approve(vesting, UINT_256_MAX), private_key)


def do_work_for_token(provider: web3.Web3, private_key: str, vesting: str, token: str, recipients: List[Recipient]):
    owner = web3.Account.from_key(private_key).address
    erc20 = provider.eth.contract(address=token, abi=erc_20_abi)

    balance_in_wei = erc20.functions.balanceOf(owner).call({"from": owner})
    symbol = erc20.functions.symbol().call({"from": owner})
    decimals = erc20.functions.decimals().call({"from": owner})
    balance = balance_in_wei / (10 ** decimals)

    logger.info(f'Current balance: wei: {balance_in_wei}, real: {balance} {symbol}')

    if balance_in_wei == 0:
        logger.error(f"Nothing to send for token: {token}, balance: {owner} = 0")
        return

    give_inf_approve(provider, private_key, vesting, token)
    addresses = [recipient.address for recipient in recipients]
    amounts = [int(float(recipient.amount) * 10 ** decimals) for recipient in recipients]
    desired_sum_in_wei = sum(float(amount) for amount in amounts)
    desired_sum = sum(float(recipient.amount) for recipient in recipients)
    remaining_balance_in_wei = balance_in_wei - desired_sum_in_wei
    remaining_balance = balance - desired_sum

    if desired_sum_in_wei == 0:
        logger.error(f"Nothing to send for token: {token}, empty recipients")
        return

    # Проверка баланса с учетом decimals
    if desired_sum_in_wei > balance_in_wei:
        logger.error(
            f"Insufficient balance for token {token}. Required in wei: {desired_sum_in_wei}, Available: {balance_in_wei}"
        )
        return

    logger.info("Distribution")
    logger.info(f"Desired amount: wei = {desired_sum_in_wei}, real = {desired_sum} {symbol}")
    logger.info(
        f"Remaining balance after distribution: wei = {remaining_balance_in_wei}, real = {remaining_balance} {symbol}"
    )

    logger.info(f'Data: ')
    for index, address in enumerate(addresses):
        amount_in_wei = amounts[index]
        amount = amount_in_wei / (10 ** decimals)
        logger.info(f'recipient: {address}, amount: wei = {amount_in_wei}, real = {amount} {symbol}')

    vesting_contract = provider.eth.contract(address=vesting, abi=vesting_abi)
    f = vesting_contract.functions.distributeRewards(
        token,
        addresses,
        amounts
    )
    utils.send_transaction(provider, f, private_key)
    logger.success(f"Distribution succeeded for token = {token}")


def do_work(fail_on_error, h: ConfigHolder):
    while True:
        logger.info("Start do work...")
        do_work_for_token(h.provider, h.private_key, h.vesting, h.token, h.recipients)
        logger.success("Processed all tokens, sleeping 10 seconds")
        h = extract_config(fail_on_error, h.token, h)
        time.sleep(10)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--token-address")
    parser.add_argument("-f", "--fail-on-error", action=argparse.BooleanOptionalAction)
    params = parser.parse_args()
    fail_on_error = params.fail_on_error
    token_address = params.token_address
    configHolder = extract_config(fail_on_error, token_address, None)
    do_work(fail_on_error, configHolder)
    logger.success("Done!")
