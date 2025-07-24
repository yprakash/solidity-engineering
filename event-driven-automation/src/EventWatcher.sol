// SPDX-License-Identifier: MIT

pragma solidity ^0.8.26;

import { Log, ILogAutomation } from "@chainlink/contracts/src/v0.8/automation/interfaces/ILogAutomation.sol";

/// @author yprakash
/// @title EventWatcher
/// @notice A Chainlink Log Trigger Automation consumer contract.
/// @dev Listens for DepositEvent and WithdrawEvent logs, and determines whether upkeep (on-chain action) is needed
contract EventWatcher is ILogAutomation {
    // event DepositEvent(address indexed msgSender);
    // event WithdrawEvent(address indexed msgSender);
    event EmittedBy(address indexed msgSender, uint256 indexed upkeepsPerformed);

    /// @dev Precomputed keccak256 signatures of the watched events.
    bytes32 constant DEPOSIT_SIG = keccak256("DepositEvent(address)");
    bytes32 constant WITHDRAW_SIG = keccak256("WithdrawEvent(address)");
    uint256 public depositCount;
    uint256 public withdrawCount;
    uint256 public upkeepsPerformed;

    constructor() {
        depositCount = 0;
        withdrawCount = 0;
        upkeepsPerformed = 0;
    }

    function bytes32ToAddress(bytes32 _address) public pure returns (address) {
        return address(uint160(uint256(_address)));
    }

    /**
     * @notice Called off-chain by Chainlink Automation nodes when a log is detected.
     * @dev Determines whether upkeep is needed based on event type and count parity.
     * @param log The log data emitted by the EventEmitter contract.
     * @param (unused) Reserved for future use (extra data).
     * @return upkeepNeeded Whether upkeep should be performed.
     * @return performData Encoded data to be passed into performUpkeep().
     */
    function checkLog(Log calldata log, bytes memory)
        external override returns(bool upkeepNeeded, bytes memory performData)
    {
        bytes32 eventSignature = log.topics[0];
        if (eventSignature == DEPOSIT_SIG) {
            depositCount += 1;
            upkeepNeeded = depositCount % 2 == 1;  // act only for odd-numbered deposits
            address logSender = bytes32ToAddress(log.topics[1]); // Extracting the sender address from the log
            performData = abi.encode(logSender);
        } else if (eventSignature == WITHDRAW_SIG) {
            withdrawCount += 1;
            upkeepNeeded = withdrawCount % 2 == 0;  // act only for even-numbered withdrawals
            address logSender = bytes32ToAddress(log.topics[1]); // Extracting the sender address from the log
            performData = abi.encode(logSender);
        } else {
            upkeepNeeded = true;
            performData = abi.encode(address(0));
        }
    }

    function performUpkeep(bytes calldata performData) external override {
        upkeepsPerformed += 1;
        address logSender = abi.decode(performData, (address));
        emit EmittedBy(logSender, upkeepsPerformed);
    }
}
