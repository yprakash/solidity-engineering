// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

contract StorageLocations {
    // State variable - stored in storage
    uint256[] permanentArray;

    function processArray(uint256[] calldata inputValues) external {
        // 'inputValues' exists in calldata - can't be modified

        // Local variable in memory - temporary copy
        uint256[] memory tempArray = new uint256[](inputValues.length);
        for (uint i = 0; i < inputValues.length; i++) {
            tempArray[i] = inputValues[i] * 2;
        }

        // Reference to storage - changes will persist
        uint256[] storage myStorageArray = permanentArray;
        myStorageArray.push(tempArray[0]); // This updates the blockchain state
    }
}

