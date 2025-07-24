// SPDX-License-Identifier: MIT

pragma solidity ^0.8.26;

/// @author yprakash
/// @title EventEmitter
/// @notice A simple contract that emits Deposit and Withdraw events.
/// @dev Used to simulate on-chain activity for Log Trigger Automation testing.
contract EventEmitter {
    /// @notice Emitted when someone calls deposit().
    /// @param msgSender The address that triggered the deposit.
    event DepositEvent(address indexed msgSender);

    /// @notice Emitted when someone calls withdraw().
    /// @param msgSender The address that triggered the withdraw.
    event WithdrawEvent(address indexed msgSender);

    constructor() {}

    function deposit() public {
        emit DepositEvent(msg.sender);
    }

    function withdraw() public {
        emit WithdrawEvent(msg.sender);
    }
}
