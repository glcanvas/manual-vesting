pragma solidity 0.8.22;

import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract Vesting {

    using SafeERC20 for IERC20;

    address public immutable owner;

    constructor() {
        owner = msg.sender;
    }


    function distributeRewards(address tokenAddress, address[] calldata destinations, uint256[] calldata amounts) external {
        require(msg.sender == owner, "Not owner");
        require(destinations.length == amounts.length, "Wrong sizes");

        IERC20 token = IERC20(tokenAddress);

        for (uint256 i = 0; i < destinations.length;) {
            token.safeTransferFrom(msg.sender, destinations[i], amounts[i]);
        unchecked {
            i++;
        }
        }
    }

}