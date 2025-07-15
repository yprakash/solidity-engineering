// SPDX-License-Identifier: MIT

pragma solidity ^0.8.19;

import { ERC20 } from "@openzeppelin/contracts@4.6.0/token/ERC20/ERC20.sol";
import { AccessControl } from "@openzeppelin/contracts@4.6.0/access/AccessControl.sol";

contract MyERC20 is ERC20, AccessControl {
    
}