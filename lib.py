from tonsdk.contract.wallet import WalletVersionEnum, Wallets
from tonsdk.utils import bytes_to_b64str
from tonsdk.crypto import mnemonic_new
# from pytoniq import LiteBalancer, WalletV4R2
# import asyncio
# from pytoniq import LiteClient
#import pytoniq
#from tonsdk.crypto import mnemonic_new
from tonsdk.contract.wallet import Wallets, WalletVersionEnum, SendModeEnum
from tonsdk.utils import to_nano, bytes_to_b64str
#import pytoniq_core
#from pytonapi import Tonapi
import asyncio
from pytonlib import TonlibClient
from tonsdk.utils import to_nano
import requests
from pathlib import Path



    #print( TOKEN)
def export_mnemonic(file):
    with open(file, 'r') as file:
        first_line = file.readline()
        first_line = first_line.replace('SEED=', '')
    wallet_mnemonics = first_line.split()
    #print(wallet_mnemonics)
    return wallet_mnemonics




async def get_seqno(client: TonlibClient, wallet_address):
    data = await client.raw_run_method(method='seqno', stack_data=[], address=wallet_address)
    return int(data['stack'][0][1], 16)



async def send(boc):
    wallet_workchain = 0
    wallet_version = WalletVersionEnum.v4r2
    wallet_mnemonics = export_mnemonic('config.txt')
    _mnemonics, _pub_k, _priv_k, wallet = Wallets.from_mnemonics(
        wallet_mnemonics, wallet_version, wallet_workchain)
    query = wallet.create_init_external_message()
    base64_boc = bytes_to_b64str(query["message"].to_boc(False))

    base = base64_boc

    raw_address = wallet.address.to_string()
    print(raw_address)

    wallet_address = wallet.address.to_string(True, True, False)

    url = 'https://ton.org/global.config.json'

    config = requests.get(url).json()

    keystore_dir = '/tmp/ton_keystore'
    Path(keystore_dir).mkdir(parents=True, exist_ok=True)

    client = TonlibClient(ls_index=14, config=config, keystore=keystore_dir, tonlib_timeout=15)
    print(wallet.address.to_string(True, True, False))

    await client.init()

    query = wallet.create_init_external_message()

    deploy_message = query['message'].to_boc(False)

    seqno = await get_seqno(client, wallet_address)
    print( seqno )
    transfer_query = wallet.create_transfer_message(to_addr='EQDSGvoktoIRTL6fBEK_ysS8YvLoq3cqW2TxB_xHviL33ex2',
                                   amount=to_nano(0.05, 'ton'), seqno=seqno, payload=boc)

    transfer_message = transfer_query['message'].to_boc(False)
    try:
        pass
        await client.raw_send_message(transfer_message)
    except Exception as e:
        print(e)


if __name__ == '__main__':
    boc=b'34234234234fdsfdsf'
    asyncio.get_event_loop().run_until_complete(send(boc))
