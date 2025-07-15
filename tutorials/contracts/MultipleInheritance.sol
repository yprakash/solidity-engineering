// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

contract BaseA {
    function getValue() public virtual pure returns (string memory) {
        return "A";
    }
}

contract BaseB {
    function getValue() public virtual pure returns (string memory) {
        return "B";
    }
}

// Multiple inheritance with function name conflict
contract Combined is BaseB, BaseA {
    // When multiple parents have functions with the same name, you must specify which ones you're overriding
    function getValue() public override(BaseB, BaseA) pure returns (string memory) {
        return "Combined";
    }
}

// Important Rule: Inheritance Order Matters
contract TokenX is BaseB, BaseA {  // BaseB comes first in the inheritance list
    function getValue() public override(BaseB, BaseA) pure returns (string memory) {
        // This calls BaseB's implementation first
        return super.getValue(); // Returns "B"
    }
}

contract TokenY is BaseA, BaseB {  // BaseA comes first in the inheritance list
    function getValue() public override(BaseA, BaseB) pure returns (string memory) {
        // This calls BaseA's implementation first
        return super.getValue(); // Returns "A"
    }
}
