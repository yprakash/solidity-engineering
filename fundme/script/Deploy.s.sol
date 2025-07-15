// SPDX-License-Identifier: MIT

pragma solidity 0.8.19;

import {Script} from "forge-std/Script.sol";
import {FundMe} from "../src/FundMe.sol";

contract Deploy is Script {
    function run() external {
        vm.startBroadcast();
        address priceFeedAddress = 0x694AA1769357215DE4FAC081bf1f309aDC325306; // Example price feed address
        new FundMe(priceFeedAddress);
        vm.stopBroadcast();
    }
}