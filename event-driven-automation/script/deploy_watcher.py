import json
import os

from w3_utils import w3, deploy_and_verify, send_tx, CHAIN_ID, ACCOUNT1

price_pair = "ETH / USD"
with open('config/price_feeds.json', 'r') as file:
    price_feed_address = json.load(file)
    price_feed_address = w3.to_checksum_address(price_feed_address[str(CHAIN_ID)][price_pair])
if not price_feed_address or not ACCOUNT1:
    print('Required env variables NOT loaded. Please check')
    exit()

myerc20_address = os.getenv('MyERC20_ADDRESS', '')
if myerc20_address:
    print('Assigning myerc20_contract object to address', myerc20_address)
    myerc20_contract = deploy_and_verify('./src/MyERC20.sol', '0.8.26', contract_address=myerc20_address)
else:  # Deploy MyERC20 contract first
    myerc20_contract = deploy_and_verify('./src/MyERC20.sol', '0.8.26', contract_name='MyERC20')

token_shop_address = os.getenv('TokenShop_ADDRESS', '')
if token_shop_address:
    print('Assigning token_shop_address object to address', token_shop_address)
    token_shop_contract = deploy_and_verify('./src/TokenShop.sol', '0.8.26', contract_address=token_shop_address)
else:  # Deploy TokenShop contract
    token_shop_contract = deploy_and_verify('./src/TokenShop.sol', '0.8.26', contract_name='TokenShop')

minter_role_hash = token_shop_contract.functions.MINTER_ROLE().call()
if myerc20_contract.functions.hasRole(minter_role_hash, token_shop_address).call():
    print('TokenShop contract already has access to mint MyERC20 tokens!')
else:
    # give your TokenShop contract the ability to “mint” your tokens from the MyERC20 contract!
    tx_receipt = send_tx(myerc20_contract.functions.grantRole(
        myerc20_contract.functions.MINTER_ROLE().call(),
        token_shop_contract.address
    ))
    print('TokenShop contract granted to mint MyERC20 tokens!')
assert myerc20_contract.functions.hasRole(minter_role_hash, token_shop_address).call()

chainlink_price = token_shop_contract.functions.getChainlinkDataFeedLatestAnswer().call()
print('Latest price of', price_pair, chainlink_price)
