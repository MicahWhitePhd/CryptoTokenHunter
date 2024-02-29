import json
import requests
import logging
import time
import random
import asyncio
import aiohttp
import pandas as pd
import os
from datetime import datetime
from aiohttp import ClientSession, TCPConnector
from requests.exceptions import ConnectionError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize logger
date_str = datetime.now().strftime("%Y-%m-%d")
logging.basicConfig(filename=f'combined_script_log_{date_str}.log', level=logging.DEBUG, force=True)

# Alchemy API URL and key
api_key = os.getenv("ALCHEMY_API_KEY")  # Load API key from .env file
alchemy_url = f"https://eth-mainnet.alchemyapi.io/v2/{api_key}"

# Headers for HTTP requests for Alchemy
alchemy_headers = {
    "accept": "application/json",
    "content-type": "application/json"
}

# Headers for HTTP requests for the security API
security_headers = {
    'Accept': '*/*',
    'Host': 'api.gopluslabs.io'
}
security_api_base_url = "https://api.gopluslabs.io/api/v1/token_security/1?contract_addresses="

# Initialize dict to save prime token data
prime_token_data = {}

# Read existing tokens from tokens.txt
with open('tokens.txt', 'r') as file:
    existing_tokens = set(line.strip() for line in file)

async def fetch_from_security_api(session, token_to_query):
    url = f"{security_api_base_url}{token_to_query}"
    retries = 3
    for _ in range(retries):
        try:
            async with session.get(url, headers=security_headers) as response:
                data = await response.json()
                if data.get("code") == 4029:
                    await asyncio.sleep(1)
                    continue
                prime_token_data[token_to_query] = data
                break
        except Exception as e:
            logging.error(f"Failed to fetch data for token {token_to_query}: {e}")
            break

async def fetch_token_security_data(wallet_transfers):
    tokens_to_query = [token for token in wallet_transfers if token not in existing_tokens]
    connector = TCPConnector(ssl=False)
    async with ClientSession(connector=connector) as session:
        tasks = []
        for token_address in tokens_to_query:
            task = asyncio.create_task(fetch_from_security_api(session, token_address))
            tasks.append(task)
        await asyncio.gather(*tasks)

    for token_data in prime_token_data.values():
        for result_key, result_value in token_data.get('result', {}).items():
            dex_info = result_value.get('dex', [])
            sorted_dex_info = sorted(dex_info, key=lambda x: float(x['liquidity']), reverse=True)
            result_value['dex'] = sorted_dex_info

def get_current_block_number():
    max_retries = 5
    retry_delay = 1
    for attempt in range(max_retries):
        try:
            payload = {
                "id": 1,
                "jsonrpc": "2.0",
                "method": "eth_blockNumber",
                "params": []
            }
            response = requests.post(alchemy_url, json=payload, headers=alchemy_headers)
            if response.status_code == 200:
                response_data = response.json()
                if 'result' in response_data:
                    return int(response_data['result'], 16)
                else:
                    logging.error("Missing 'result' in response")
                    return None
            else:
                logging.error(f"Error in response: {response.status_code}")
                return None

        except ConnectionError as e:
            logging.warning(f"Connection error on attempt {attempt + 1}: {e}")
            time.sleep(retry_delay)
            retry_delay *= 2

    logging.error("Max retries reached. Failed to get current block number.")
    return None

def main():
    print("Starting the main process...")
    date_str = datetime.now().strftime("%Y-%m-%d")
    current_block_number = get_current_block_number()
    if current_block_number is None:
        logging.error("Unable to get current block number. Exiting.")
        print("Failed to get current block number. Check logs for details.")
        return
    else:
        print(f"Current block number: {current_block_number}")

    block_number_8000_blocks_ago = current_block_number - 8000
    print(f"Block number 8000 blocks ago: {block_number_8000_blocks_ago}")

    token_addresses = set()  # Initialize a set to store unique token addresses
    
    with open(f'found-tokens_{date_str}.txt', 'a') as token_file:
        with open('wallet.txt', 'r') as file:
            wallet_addresses = [line.strip() for line in file if line.strip()]
        print(f"Total wallet addresses to process: {len(wallet_addresses)}")
        random.shuffle(wallet_addresses)

        for address in wallet_addresses:
            print(f"Processing address: {address}")
            next_page_key = None
            max_retries = 5
            retry_delay = 1

            for attempt in range(max_retries):
                try:
                    payload_params = {
                        "fromBlock": hex(block_number_8000_blocks_ago),
                        "toBlock": "latest",
                        "category": ["erc20"],
                        "toAddress": address,
                        "excludeZeroValue": True,
                        "maxCount": "0x3e8"
                    }

                    if next_page_key:
                        payload_params["pageKey"] = next_page_key

                    payload = {
                        "id": 1,
                        "jsonrpc": "2.0",
                        "method": "alchemy_getAssetTransfers",
                        "params": [payload_params]
                    }
                    
                    response = requests.post(alchemy_url, json=payload, headers=alchemy_headers)
                    logging.debug(f"Complete Alchemy API Response for address {address}: {response.json()}")
                    if response.status_code == 200:
                        response_json = response.json().get('result', {})
                        transfers = response_json.get('transfers', [])
                        logging.debug(f"Transfers for address {address}: {transfers}")
                        for transfer in transfers:
                            asset = transfer.get('asset', 'Unknown')
                            token_address = transfer['rawContract']['address']
                            token_addresses.add(token_address)  # Add token address to the set
                            token_file.write(f"{address} - {token_address} - {asset}\n")

                except ConnectionError as e:
                    logging.warning(f"Connection error on attempt {attempt + 1}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        logging.error(f"Max retries reached for address {address}.")
                        break

            print(f"Completed processing address: {address}")

    print("Fetching token security data...")
    asyncio.run(fetch_token_security_data(token_addresses))  # Pass token addresses
    print("Completed fetching token security data.")

    # Save the prime token data to a JSON file
    date_str = datetime.now().strftime("%Y-%m-%d")
    json_file_path = f'prime_token_data_{date_str}.json'
    with open(json_file_path, 'w') as f:
        json.dump(prime_token_data, f, indent=4)

    # Processing the data for CSV export
    extracted_data = []
    for address, content in prime_token_data.items():
        result = content.get('result', {})
        for addr, details in result.items():
            if addr == address:
                token_name = details.get('token_name', '')
                token_symbol = details.get('token_symbol', '')
                dex_list = details.get('dex', [])
                for dex in dex_list:
                    liquidity = dex.get('liquidity', 0)
                    extracted_data.append([address, token_name, token_symbol, float(liquidity)])

    # Creating a DataFrame and saving to CSV
    df = pd.DataFrame(extracted_data, columns=['address', 'token_name', 'token_symbol', 'liquidity'])
    df = df.drop_duplicates(subset=['address'])
    df = df.sort_values(by='liquidity', ascending=False)
    csv_file_path = f'extracted_token_data_{date_str}.csv'
    df.to_csv(csv_file_path, index=False)

    print("Data processing complete. Check the output files.")

if __name__ == "__main__":
    main()
