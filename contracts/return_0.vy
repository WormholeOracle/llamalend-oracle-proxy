# @version 0.3.10
"""
@title Dummy Oracle
@notice Always returns 0 for price(), returns 1 for price_w()
"""

@external
@view
def price() -> uint256:
    return 1128609365938736600
    # raise "Forced revert"

@external
def price_w() -> uint256:
    # raise "Forced revert"
    return 1
