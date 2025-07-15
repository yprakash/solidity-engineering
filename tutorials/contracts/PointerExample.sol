// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

contract PointerExample {
    // State array in storage
    uint256[] public storageArray = [1, 2, 3];

    function manipulateArray() public returns (uint256) {
        // This creates a pointer to the storage array
        uint256[] storage storageArrayPointer = storageArray;

        // This modifies the actual storage array through the pointer
        storageArrayPointer[0] = 100;

        // At this point, storageArray is now [100, 2, 3]
 
        // This creates a copy in memory, not a pointer to storage
        uint256[] memory memoryArray = storageArray;
 
        // This modifies only the memory copy, not the storage array
        memoryArray[1] = 200;

        // At this point, storageArray is still [100, 2, 3]
        // and memoryArray is [100, 200, 3]
        return memoryArray[1];
    }
}

