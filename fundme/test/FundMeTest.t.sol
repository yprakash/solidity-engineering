// SPDX-License-Identifier: MIT

pragma solidity 0.8.19;

import {Test, console} from "forge-std/Test.sol";
import {FundMe} from "../src/FundMe.sol";

contract FundMeTest is Test {
    FundMe fundMe;

    function setUp() external {
        address priceFeedAddress = 0x694AA1769357215DE4FAC081bf1f309aDC325306; // Example price feed address
        fundMe = new FundMe(priceFeedAddress);
    }

    function testOwnerIsMsgSender() public {
        assertEq(fundMe.getOwner(), address(this), "Owner should be the contract deployer");
    }

    function testPriceFeedVersion() public {
        uint256 version = fundMe.getVersion();
        console.log("Price feed version:", version);
        assertEq(version, 4, "Price feed version should be greater than 0");
    }
}