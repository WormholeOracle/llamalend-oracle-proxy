import warnings

from brownie import Contract, accounts, chain, CryptoFromPoolsVaultWAgg, OracleProxy, AMM

warnings.filterwarnings("ignore")

# This script tests the deployment of the OracleProxy.vy contract with the CryptoFromPoolsVaultWAgg.vy implementation contract
# It deploys a test LlamaLend market with oracle_impl, then sets to oracle_impl2 in the proxy
# It checks that price() returns a good value and changes the oracle price to check price_w() updates properly in the AMM
# Note that there is a deviation check when setting a new oracle_impl, if it exceeds the value specified in the proxy, it will revert

# LlamaLend factory
factory = Contract('0xeA6876DDE9e3467564acBeE1Ed5bac88783205E0')

def deploy():

	#Dola/sUSDe, sUSDe/crvUSD w/ sDOLA vault and crvUSD agg = sDOLA/crvUSD
	oracle_impl = CryptoFromPoolsVaultWAgg.deploy(
		['0x744793B5110f6ca9cC7CDfe1CE16677c3Eb192ef', 
		'0x57064F49Ad7123C92560882a45518374ad982e85'], # pools
		[1,0], #borrowed
		[0,1], #collateral
		'0xb45ad160634c528Cc3D2926d9807104FA3157305', #vault
		'0x18672b1b0c623a30089A280Ed9256379fb0E4E62', #agg
		{'from': accounts[0]}
	)

	# DOLA/USR, USR/USDC, USDC/crvUSD pools w/ sDOLA vault and crvUSD agg = sDOLA/USD
	oracle_impl2 = CryptoFromPoolsVaultWAgg.deploy(
		['0x38De22a3175708D45E7c7c64CD78479C8B56f76E', 
		'0x3eE841F47947FEFbE510366E4bbb49e145484195', 
		'0x4DEcE678ceceb27446b35C672dC7d61F30bAD69E'], # pools
		[1,1,1], #borrowed
		[0,0,0], #collateral
		'0xb45ad160634c528Cc3D2926d9807104FA3157305', #vault
		'0x18672b1b0c623a30089A280Ed9256379fb0E4E62', #agg
		{'from': accounts[0]}
	)

	# Deploy the Proxy contract, using the factory's address to get the admin
	proxy = OracleProxy.deploy(
		oracle_impl.address, # implementation
		factory.address, # factory
		500, # Max deviation in BPS
		{'from': accounts[0]}
	)

	# Deploy LlamaLend market using proxy as oracle
	market = factory.create(
		'0xf939E0A03FB07F59A73314E73794Be0E57ac1b4E', # borrowed
		'0xa3931d71877C0E7a3148CB7Eb4463524FEc27fbD', # collateral
		300, # A
		2000000000000000, # fee
		13000000000000000, # loan_discount
		10000000000000000, # liq_discount
		proxy, # oracle
		'sdeUSD', # name
		31709791, # min_rate
		7927447995, # max_rate
		{'from': accounts[0]}
	)

	return market, proxy, oracle_impl2

def test():

	# deploy all oracles and test market
	market, proxy, oracle_impl2 = deploy()

	amm = AMM.at(market.events["NewVault"]["amm"])
	price_oracle_proxy = amm.price_oracle_contract()
	impl = OracleProxy.at(price_oracle_proxy).implementation()

	price = amm.price_oracle() /1e18


	print("_____IMPL1 INSTANTIATED_____")
	print(f"Market oracle proxy at address {price_oracle_proxy}")
	print(f"Proxy implementation at address {impl}")
	print(f"Oracle price in AMM is {price}")

	admin = accounts.at(factory.admin(), force=True)

	# set impl2
	proxy.set_price_oracle(oracle_impl2.address, {'from': admin})

	price_oracle_proxy = amm.price_oracle_contract()
	impl = OracleProxy.at(price_oracle_proxy).implementation()
	price = amm.price_oracle() / 1e18

	print("_____IMPL2 INSTANTIATED_____")
	print(f"Market oracle proxy at address {price_oracle_proxy}")
	print(f"Proxy implementation at address {impl}")
	print(f"Oracle price in AMM is {price}")

	#Dummy echange to test price_w()
	dola_whale = accounts.at('0xE5f24791E273Cb96A1f8E5B67Bc2397F0AD9B8B4', force=True)
	dola_usr = Contract('0x38De22a3175708D45E7c7c64CD78479C8B56f76E')
	dola = Contract('0x865377367054516e17014CcdED1e7d814EDC9ce4')
	dola.approve(dola_usr,100000000e18, {'from': dola_whale})
	dola_usr.exchange(0,1,25000000e18,0,dola_whale, {'from':dola_whale})
	chain.sleep(86400)

	amm.exchange(0,1,0,0,accounts[0], {'from': accounts[0]})
	price = amm.price_oracle() / 1e18

	print(f"_____Price_w TEST_____")
	print(f"After manipulating DOLA/USR price oracle and calling exchange in AMM (price_w call), price in AMM is {price}")