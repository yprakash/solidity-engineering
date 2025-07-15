// SPDX-License-Identifier: MIT

// 1. Deploy mocks when we are on a local anvil chain
// 2. keep track of the contract address across different chains
// Sepolia ETH/USD
// Mainnet ETH/USD

pragma solidity 0.8.19;

import {Script} from "forge-std/Script.sol";

contract HelperConfig is Script {
    // If we are on a local anvil chain, we will deploy mocks
    // Otherwise, grab the existing address from the live network
    struct Config {
        address priceFeedAddress;
    }

    Config public activeConfig;
    mapping (uint => address) chainIdToPriceFeedAddress;

    constructor() {
        // Set the price feed address for the Sepolia testnet
        activeConfig = Config({
            priceFeedAddress: 0x694AA1769357215DE4FAC081bf1f309aDC325306 // Example price feed address
        });
    }

    function getActiveConfig() external view returns (Config memory) {
        return activeConfig;
    }
}