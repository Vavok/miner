import asyncio
import random
from pytoniq import LiteBalancer, WalletV4R2
from pytoniq_core import Address, Cell
from pytoniq_core.boc.deserialize import BocError
from subprocess import Popen, PIPE, STDOUT
from tonsdk.contract.wallet import Wallets, WalletVersionEnum, SendModeEnum
import requests,re,time,os
from subprocess import Popen, PIPE, STDOUT
import requests,re,time,os
from pytonapi import Tonapi
import signal
from lib import *
import random
import binascii
from pytoniq import Cell
import threading
import psutil
import datetime
from ton import TonlibClient
import shutil


# Получаем текущую дату и время
now = datetime.datetime.now().strftime("%H:%M:%S ")
print(now)


def export_mnemonic(file):
    with open(file, 'r') as file:
        first_line = file.readline()
        first_line = first_line.replace('SEED=', '')
    wallet_mnemonics = first_line.split()
    return wallet_mnemonics

MNEMONICS = export_mnemonic('config.txt')
file_givers='givers100.txt'
giver_address =giverslist(file_givers)
with open('config.txt', 'r') as file:
    r=file.readlines()
    TOKEN=r[1].replace('TONAPI_TOKEN=','')
    TOKEN = TOKEN.replace('\n', '')
    gpu_count=r[2].replace('gpu_count=','')
    gpu_count=int(gpu_count)
    print('gpu_count=',gpu_count)
def adress(mnemonic):
    wallet_workchain = 0
    wallet_version = WalletVersionEnum.v4r2
    wallet_mnemonics = export_mnemonic('config.txt')
    _mnemonics, _pub_k, _priv_k, wallet = Wallets.from_mnemonics(
        wallet_mnemonics, wallet_version, wallet_workchain)
    wallet_address = wallet.address.to_string(True, True, False)
    return wallet_address

def refresh(tonapi):
    global seed, complexity, iterations, giver_address
    try:
        b = tonapi.blockchain.execute_get_method(giver_address, 'get_pow_params')
        num_hex = b.stack[0].num
        seed = int(num_hex, 16)
        #  print(seed)
        complexity = int(b.stack[1].num, 16)
        iterations = int(b.stack[2].num, 16)
    except Exception as e:
        print('TUT', str(e))


def refresh_tonapi(tonapi):
    global seed, complexity,  iterations, giver_address
    while True:
        refresh(tonapi)
        time.sleep(3)

tonapi = Tonapi(api_key=TOKEN)
seed,complexity,iterations=0,0,0
t0 = threading.Thread(target=refresh_tonapi,args=(tonapi,))
t0.start()  # В ОТДЕЛЬНОМ ПОТОКОЕ ЗАПУСКАЕМ ПОЛУЧЕНИЯ ЗАДАНИЙ ОТ ГИВЕРА
provider = LiteBalancer.from_mainnet_config(trust_level=2)

wallet_mnemonics = export_mnemonic('config.txt')

wallet_address=adress(wallet_mnemonics)
print('your adress=',wallet_address)

async def get_pow_params(giver_address: str) -> tuple[int, int, int]:
    response = await provider.run_get_method(giver_address, "get_pow_params", [])
    return response[0], response[1], response[2]  # seed complexity iterations




async def send(wallet: WalletV4R2, giver_address: str, boc: bytes) -> None:
    # try:
    transfer_message = wallet.create_wallet_internal_message(
        destination=Address(giver_address),
        value=int(0.05 * 1e9),
        body=Cell.from_boc(boc)[0].to_slice().load_ref(),
    )

    await wallet.raw_transfer(msgs=[transfer_message])
# except BocError:
#     ...
# except Exception:
#     raise


async def main_send(MNEMONICS,n) -> None:
# try:
    await provider.start_up()
    global seed, complexity,  iterations, giver_address
    wallet = await WalletV4R2.from_mnemonic(provider, MNEMONICS)
    ## Определение операционной системы
    operating_system = os.name

    if operating_system == 'posix':
        path_to_exe = 'pow-miner-cuda'
    elif operating_system == 'nt':
        print("Windows")
        path_to_exe = 'pow-miner-cuda.exe'
    else:
        print("Не удалось определить операционную систему")
        path_to_exe = 'pow-miner-cuda'
   # path_to_exe = 'pow-miner-cuda'
    wallet_address = adress(MNEMONICS)

    # Замените значения параметров на фактические
    gpu_id = '0'
    test_time = '9999'
    i=0

    a = await get_pow_params(giver_address)
    #print('seed=',a[0], a[1], a[2])

    # if seed == a[0] :
    #     print('Good')
    miner_on=True
    k,catch = 0,0
    find=False
    seed_mine=0
    complexity_miner = 0
    iterations_mine=0


    pattern = r"(\d+.\d+) Mhash/s"
    while miner_on:
        # try:
        match=False
        refresh(tonapi)
        while seed==seed_mine:
            print('задание ещё не поменялось')
            time.sleep(1)

        #path = f"bocs/{random.randint(1, 150)}.boc"
        seed_mine=seed
        complexity_miner = complexity
       # iterations_mine=iterations
        iterations_mine=999999999999
        print(f'новое задание seed={seed_mine}  complexity_miner={complexity_miner} iterations={iterations} ')


        procs, path=[], []

        for g in range(n):
            path.append(f"bocs/{g}.boc")
            cmd = f'{path_to_exe} -vv -g {g} -F 512 -t {test_time} {wallet_address} {seed_mine} {complexity_miner} {iterations_mine} {giver_address} {path[g]}'
            p = Popen(
                cmd,
                stdout=PIPE,
                stderr=STDOUT,
                shell=True,
                encoding='utf-8',
                errors='replace'
            )
            procs.append(p)
        found = False
        poisk=True
        while poisk:
            boc=False
            realtime_outputs,matchs=[],[]
            try:
                for j in range(n):
                    #print(j)
                    realtime_output = procs[j].stdout.readline()
                    realtime_outputs.append(realtime_output)
                    match = re.search(pattern, realtime_output)
                    if match:
                        matchs.append(match.group(0))
                smart_megahash = sum([float(value.split()[0]) for value in matchs])
                matchs.append(f'Всего= {smart_megahash} Mhash/s | найдено решений = {catch}')
            except Exception as e:
                print(str(e))
            k += 1

            if match:
                try:
                    now = datetime.datetime.now().strftime("%H:%M:%S ")
                    string=f'{k} |   {now} |'
                    for j in range(n+1):
                        if j==n:
                            string += f' {matchs[j]}  '
                        else:
                            string+= f' gpu{j} =  {matchs[j]} | '
                    print(string)
                except:
                    print(...)

            if seed_mine != seed:
                close_miner()
                poisk = False
                break

            for filename in path:
                if os.path.exists(filename):
                    print(f"'----------------=============РЕШЕНИЕ НАЙДЕНО==============-----------------------\nФайл {filename} существует.")

                    if os.access(filename, os.R_OK | os.W_OK):
                        print(f"У вас есть доступ к чтению и записи файла {filename}.")
                    else:
                        print(f"У вас нет доступа к чтению или записи файла {filename}.")
                    close_miner()
                    while not boc:
                        try:
                            boc = Path(filename).read_bytes()
                            print('boc',boc)
                        except Exception as e:
                            print('не читается бок',str(e))
                            time.sleep(0.07)
                    print(filename)
                    shutil.copyfile(filename, f'bocstmp/0.boc')
                    os.remove(filename)
                    otpravitsya=False
                    while not otpravitsya:
                        try:
                            await send(wallet, giver_address,boc)
                            print('отправил')
                            otpravitsya=True
                        except Exception as e:
                            print(f'НЕ СМОГ ОТПРАВИТЬ РЕШЕНИЕ {str(e)}')
                            time.sleep(0.05)

                    close_miner()
                    catch += 1
                    find = True
                    poisk = False
                    break
            if find:
                find = False
                print('трам пам пам зачем я тут?')
                giver_address = giverslist(file_givers)
                giver_address = giverslist(file_givers)
                refresh(tonapi)
                time.sleep(1)
                break


        # except Exception as e:
        #     print('большое исключение'+str(e))




if __name__ == "__main__":

    asyncio.run(main_send(wallet_mnemonics,gpu_count))