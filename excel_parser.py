# Функция для чтения и парсинга Excel файла
from typing import List

import pandas as pd
import web3

from models.recipient import Recipient


def parse_excel(file_path) -> List[Recipient]:
    df = pd.read_excel(file_path)

    if 'address' not in df.columns or 'count' not in df.columns:
        raise ValueError("Excel file must contain 'web 3 address' and 'token count for address' columns")

    data = []
    for index, row in df.iterrows():
        address = web3.Web3.to_checksum_address(row['address'])
        amount = row['count']
        model = Recipient(address, amount)
        data.append(model)

    return data
