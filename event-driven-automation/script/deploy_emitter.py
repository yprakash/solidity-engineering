from utils.w3_utils import ACCOUNT1, deploy_and_verify, load_deployed_contract, send_tx

contract_address = '0x38116496A209Fd12461BE612CA0aC63096F2f675'
src_path = './event-driven-automation/src/'
if contract_address:
    print('Assigning emit_contract object to address', contract_address)
    emit_contract = load_deployed_contract(contract_address, src_path + 'EventEmitter.sol', '0.8.26')
else:
    emit_contract = deploy_and_verify(src_path + 'EventEmitter.sol', '0.8.26')

tx_receipt = send_tx(emit_contract.functions.deposit())
# Decode the logs for DepositEvent
events = emit_contract.events.DepositEvent().process_receipt(tx_receipt)

assert len(events) > 0, "DepositEvent not emitted"
assert events[0]['args']['msgSender'] == ACCOUNT1, "Unexpected sender"
