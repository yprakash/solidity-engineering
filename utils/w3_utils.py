"""
This module provides utility functions for interacting with the Ethereum blockchain using Web3.py.
It includes functions for compiling Solidity contracts, sending transactions,
encoding constructor arguments, and deploying and verifying contracts on Etherscan.
"""
import json
import os
import tomllib
from time import sleep

import requests
import solcx
from dotenv import load_dotenv
from eth_abi import encode
from eth_utils import to_hex
from web3 import Web3

load_dotenv('.env')
load_dotenv('.env.sepolia')

# Initialize Web3 connection
w3 = Web3(Web3.HTTPProvider(os.getenv('PROVIDER_URL')))
if w3.is_connected():
    print("Successfully connected to the provider!")
else:
    print("Failed to connect to the given provider ", os.getenv('PROVIDER_URL'))
    exit()

# Load essential environment variables
_PRIVATE_KEY = os.getenv('PRIVATE_KEY')
CHAIN_ID = int(os.getenv('CHAIN_ID', 11155111))  # Default to Sepolia testnet
ACCOUNT1 = w3.to_checksum_address(os.getenv('ACCOUNT1'))
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')
BASE_URL = "https://api.etherscan.io/v2/api"

# Constants used as keys in transactions and API payloads
KEY_abi = 'abi'
KEY_chainId = 'chainId'
KEY_contractAddress = 'contractAddress'
KEY_from = 'from'
KEY_nonce = 'nonce'
KEY_status = 'status'
KEY_to = 'to'
SLEEP_TIME = 2  # Time to wait between retries (in seconds)


def compile_contract(contract_path: str, version: str, contract_name: str = None):
    """
    Compiles a Solidity contract using the specified version of the Solidity compiler.
    Args:
        contract_path (str): Relative Path to the Solidity contract file.
        version (str): Version of the Solidity compiler to use. 0.8.24
        contract_name (str, optional): Name of the contract to compile. Defaults to None.
    Returns:
        dict: Compiled contract interface containing ABI and bytecode.
    """
    if version not in (v.public for v in solcx.get_installed_solc_versions()):
        solcx.install_solc(version)
        print(f"Installed solc version {version}")
    solcx.set_solc_version(version=version)
    with open(contract_path, 'r') as file:
        contract_source = file.read()

    compiled_sol = None
    # Check for remappings in foundry.toml if it exists
    if os.path.exists("foundry.toml"):
        with open("foundry.toml", "rb") as f:
            foundry_config = tomllib.load(f)
            remappings = foundry_config["profile"]["default"].get("remappings", [])
            if remappings:
                print('found remappings in foundry.toml:', remappings)
                compiled_sol = solcx.compile_source(contract_source, import_remappings=remappings)

    # Compile the contract if no remappings were found or compilation failed
    if not compiled_sol:
        compiled_sol = solcx.compile_source(contract_source)

    # Determine the contract name if not provided
    if contract_name is None:  # Take the first contract if no name is provided
        contract_name = next(iter(compiled_sol))
    else:
        contract_name = f'<stdin>:{contract_name}'

    # Extract the compiled contract interface
    contract_interface = compiled_sol[contract_name]
    print(f'Compiled {contract_path} for contract {contract_name}')
    return contract_interface


def send_tx(transaction, build_tx=True):
    """
    Sends a transaction to the Ethereum blockchain.
    Args:
        transaction (dict): Transaction object to send.
        build_tx (bool): Whether to build the transaction. Defaults to True.
    Returns:
        dict: Transaction receipt containing details of the mined transaction.

    NOTE: It waits til the transaction is mined and returns the receipt.
    We have 1-line .transact() for state changes, but it works only if you are using a local node like Ganache, Anvil
    Or your account is unlocked in the node (like Infura), which is rare in public networks. So we need below steps
    """
    nonce = w3.eth.get_transaction_count(ACCOUNT1, 'pending')  # To include unmined txs, Use pending
    if build_tx:
        transaction = transaction.build_transaction({
            KEY_from: ACCOUNT1,
            KEY_chainId: CHAIN_ID,
            KEY_nonce: nonce
        })
    else:  # For pre-encoded calldata
        transaction[KEY_chainId] = CHAIN_ID
        transaction[KEY_from] = ACCOUNT1
        transaction[KEY_nonce] = nonce

    signed_tx = w3.eth.account.sign_transaction(transaction, private_key=_PRIVATE_KEY)
    txn_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f'Sent transaction to chain {CHAIN_ID} with nonce {nonce} hash {txn_hash}')
    tx_receipt = w3.eth.wait_for_transaction_receipt(txn_hash)
    assert tx_receipt[KEY_status] == 1
    return tx_receipt


def encode_constructor_args(abi, constructor_args: list = None):
    """
    Encodes constructor arguments for a contract deployment.
    Args:
        abi (list): ABI of the contract containing constructor details. For example
        [{
          "type":"constructor",
          "stateMutability":"payable",
          "inputs":[{
                "type":"address","name":"_logic","internalType":"address"
             }, {
                "type":"bytes","name":"_data","internalType":"bytes"
             }
          ]
        }]
        constructor_args (list, optional): List of arguments for the constructor. Defaults to None.
    Returns:
        str: Hexadecimal string of encoded constructor arguments.
    """

    if constructor_args is None:
        constructor_args = []
    # Constructor arguments must be ABI-encoded manually, based on ABI + your constructor args.
    constructor_inputs = next(
        (item['inputs'] for item in abi if item['type'] == 'constructor'), []
    )
    types = [i['type'] for i in constructor_inputs]
    encoded = encode(types, constructor_args)  # eth_abi.encode
    hex_constructor_args = to_hex(encoded)[2:]  # Remove '0x'
    print(f"hex_constructor_args {hex_constructor_args}")
    return hex_constructor_args


def load_verified_contract(
        contract_address: str,  # The Ethereum address of the contract
        apikey: str = ETHERSCAN_API_KEY,  # Etherscan API key. Defaults to ETHERSCAN_API_KEY from .env
        cache_dir: str = "./.abi_cache"  # Directory to store cached ABI files. Defaults to "./.abi_cache".
):
    """
    Loads a verified contract from Etherscan by its address and caches the ABI locally to avoid repeated API calls.
    Returns: web3.contract.Contract: A Web3 contract object for interacting with the contract.
    Raises: ValueError: If the ABI cannot be fetched from Etherscan.
    """
    contract_address = w3.to_checksum_address(contract_address)
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"{contract_address}.json")

    # Load ABI from cache if available
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            abi = json.load(f)
    else:
        # Fetch from Etherscan
        url = f"{BASE_URL}?module=contract&action=getabi&chainid={CHAIN_ID}&address={contract_address}&apikey={apikey}"
        response = requests.get(url)
        data = response.json()
        if data["status"] != "1":
            raise ValueError(f"Failed to fetch ABI for {contract_address}: {data['result']}")
        abi = json.loads(data["result"])
        with open(cache_path, "w") as f:
            json.dump(abi, f, indent=2)

    return w3.eth.contract(address=contract_address, abi=abi)


def load_deployed_contract(
        contract_address: str,  # The Ethereum address of the deployed contract.
        contract_path: str,  # Relative path to the Solidity contract file.
        version: str,  # Version of the Solidity compiler to use (e.g., '0.8.24')
        contract_name: str = None  # Name of the contract to load. None uses the first contract in the compiled source.
):
    """
    Loads a deployed contract by compiling its source code and associating it with the given address.
    Returns: web3.contract.Contract: A Web3 contract object for interacting with the deployed contract.
    """
    contract_interface = compile_contract(contract_path, version, contract_name)
    contract_address = w3.to_checksum_address(contract_address)
    return w3.eth.contract(address=contract_address, abi=contract_interface[KEY_abi])


def deploy_and_verify(
        contract_path: str,  # Relative contract path
        version: str,  # Solidity version like '0.8.24'
        contract_name: str = None,  # Name of contract if .sol file has dependencies/multiple contracts
        constructor_args: list = None,  # Constructor arguments to deploy
        contract_address: str = None  # Directly verify if contract is already deployed
):
    """
    Deploys a Solidity contract to the Ethereum blockchain and verifies it on Etherscan.
    Args:
        contract_path (str): Relative Path to the Solidity contract file.
        version (str): Version of the Solidity compiler to use.
        contract_name (str, optional): Name of the contract to deploy. Defaults to None.
        constructor_args (list, optional): Arguments for the contract constructor. Defaults to None.
        contract_address (str, optional): Address of an already deployed contract for verification. Defaults to None.
            when None, it deploys the contract first.
    NOTE: flattened .sol file must have already been generated by using 'forge flatten' command and saved in 'flat/'.
    Returns:
        web3.eth.Contract: Web3 contract object for the deployed contract.
    """
    flattened_path = contract_path.replace('src/', 'flat/flatten_')
    if not os.path.exists(flattened_path):
        raise Exception(f"Can NOT find source code in {flattened_path}, Please check")

    contract_interface = compile_contract(contract_path, version, contract_name)
    full_version_string = f"v{solcx.get_solc_version(with_commit_hash=True)}"
    if contract_name is None:  # Take the first contract if no name is provided
        contract_name = next(iter(contract_interface))

    if contract_address:
        print(f"Preparing to verify contract at address {contract_address}")
    else:
        contract = w3.eth.contract(abi=contract_interface[KEY_abi], bytecode=contract_interface['bin'])
        if constructor_args:
            tx_receipt = send_tx(contract.constructor(*constructor_args))
        else:
            tx_receipt = send_tx(contract.constructor())
        contract_address = tx_receipt[KEY_contractAddress]
        print('========== ========== NOTE ========== ==========')
        print(f"Deployed {contract_path} Please take a note of contract_address: {contract_address}")
        print('========================================')

    print(f"Reading flattened_path from {flattened_path}")
    with open(flattened_path, "rb") as file:
        source_code = file.read()

    encoded_args = encode_constructor_args(contract_interface[KEY_abi], constructor_args)
    payload = {
        'chainid': CHAIN_ID,  # should be chainid not chainId
        "action": "verifysourcecode",
        "apikey": ETHERSCAN_API_KEY,
        "codeformat": "solidity-single-file",
        "compilerversion": full_version_string,
        "constructorArguements": encoded_args,  # note the spelling mistake in Etherscan API!
        "contractaddress": contract_address,
        "contractname": contract_name,
        "licenseType": 3,  # MIT
        "module": "contract",
        "optimizationUsed": 1,
        "runs": 200,
        "sourceCode": source_code,
    }
    print(f"Verifying contract payload {payload}")

    resp = requests.post(BASE_URL, data=payload)
    result = resp.json()
    print("Initial response:", result)

    if result[KEY_status] != "1":
        raise Exception("Verification submission failed: " + result["result"])
    guid = result["result"]
    print("Verification submission successful, GUID:", guid)

    # Poll for verification result
    for _ in range(10):
        sleep(SLEEP_TIME)
        status_payload = {
            "apikey": ETHERSCAN_API_KEY,
            "module": "contract",
            "action": "checkverifystatus",
            "guid": guid,
        }
        status_resp = requests.get(BASE_URL, params=status_payload)
        status = status_resp.json()
        print("Verification check:", status)

        if status[KEY_status] == "1":
            print("✅ Contract verified!")
            break
        elif "Pending" in status["result"]:
            print("🔄 Verification is still pending, waiting...")
        else:
            raise Exception("❌ Verification failed: " + status["result"])

    return w3.eth.contract(address=contract_address, abi=contract_interface[KEY_abi])
