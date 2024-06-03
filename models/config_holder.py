from dataclasses import dataclass

import web3
from eth_typing import ChecksumAddress


@dataclass
class ConfigHolder:
    provider: web3.Web3
    private_key: str
    vesting: str
    token: ChecksumAddress
    recipients: list
