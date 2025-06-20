# ============================================================================
# Imports and Setup
# ============================================================================
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from web3 import Web3, HTTPProvider

import os
from dotenv import load_dotenv
import logging
import hmac
import hashlib
from datetime import datetime
import asyncio
import httpx
from typing import Optional, Tuple, Dict
from eth_account import Account
import uvicorn
import logging.handlers
import queue
import threading
from supabase import create_client, Client

# ============================================================================
# Async Logging Setup (WARNING and ERROR only)
# ============================================================================
log_queue = queue.Queue(-1)
queue_handler = logging.handlers.QueueHandler(log_queue)

# Set up the root logger to only handle WARNING and above
logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
logger.handlers = []  # Remove default handlers
logger.addHandler(queue_handler)

# File handler for warnings and errors
file_handler = logging.FileHandler("bot.log")
file_handler.setLevel(logging.WARNING)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

# Listener to process log records asynchronously
listener = logging.handlers.QueueListener(log_queue, file_handler)
listener.start()

# Note: Only WARNING and ERROR logs will be written to bot.log. INFO/DEBUG logs are suppressed.

# ============================================================================
# Environment Variables
# ============================================================================
load_dotenv()
MONAD_TESTNET_RPC_URL = os.getenv("MONAD_TESTNET_RPC_URL")
BOT_USERNAME = os.getenv("BOT_USERNAME")
BOT_FID = os.getenv("BOT_FID")
NEYNAR_API_KEY = os.getenv("NEYNAR_API_KEY")
NEYNAR_WEBHOOK_SECRET = os.getenv("NEYNAR_WEBHOOK_SECRET")


FACTORY_ADDRESS = os.getenv("FACTORY_ADDRESS")
TIP_BOT_PRIVATE_KEY = os.getenv("TIP_BOT_PRIVATE_KEY")
TIP_BOT_ADDRESS = os.getenv("TIP_BOT_ADDRESS")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Missing Supabase credentials")
    raise ValueError("Missing Supabase credentials")
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}")
    raise

# ============================================================================
# Web3 Setup
# ============================================================================
w3 = Web3(HTTPProvider(MONAD_TESTNET_RPC_URL))
if not w3.is_connected():
    logger.error("Failed to connect to Monad Testnet RPC")
    raise Exception("Failed to connect to Monad Testnet RPC")

# ============================================================================
# Token Configuration
# ============================================================================
SUPPORTED_TOKENS = {
    "MON": {"address": "0x0000000000000000000000000000000000000000", "decimals": 18},
    "USDC": {"address": "0xf817257fed379853cDe0fa4F97AB987181B1E5Ea", "decimals": 6},
    "USDT": {"address": "0x88B8E2161DEDC77EF4AB7585569D2415A1C1055D", "decimals": 6},
    "BEAN": {"address": "0x268E4E24E0051EC27B3D27A95977E71CE6875A05", "decimals": 18},
    "BMONAD": {"address": "0x3552F8254263EA8880C7F7E25CB8DBBD79C0C4B1", "decimals": 18},
    "CHOG": {"address": "0xE0590015A873BF326BD645C3E1266D4DB41C4E6B", "decimals": 18},
    "DAK": {"address": "0x0F0BDEBF0F83CD1EE3974779BCB7315F9808C714", "decimals": 18},
    "HALLI": {"address": "0x6CE1890EEADAE7DB01026F4B294CB8EC5ECC6563", "decimals": 18},
    "HEDGE": {"address": "0x04A9D9D4AEA93F512A4C7B71993915004325ED38", "decimals": 18},
    "JAI": {"address": "0xCC5B42F9D6144DFDFB6FB3987A2A916AF902F5F8", "decimals": 6},
    "KEYS": {"address": "0x8A056DF4D7F23121A90ACA1CA1364063D43FF3B8", "decimals": 18},
    "MAD": {"address": "0xC8527E96C3CB9522F6E35E95C0A28FEAB8144F15", "decimals": 18},
    "MAD-LP": {"address": "0x786F4AA162457ECDF8FA4657759FA3E86C9394FF", "decimals": 18},
    "MIST": {"address": "0xB38BB873CCA844B20A9EE448A87AF3626A6E1EF5", "decimals": 18},
    "MONDA": {"address": "0x0C0C92FCF37AE2CBCC512E59714CD3A1A1CBC411", "decimals": 18},
    "MOON": {"address": "0x4AA50E8208095D9594D18E8E3008ABB811125DCE", "decimals": 18},
    "NOM": {"address": "0x43E52CBC0073CAA7C0CF6E64B576CE2D6FB14EB8", "decimals": 18},
    "NSTR": {"address": "0xC85548E0191CD34BE8092B0D42EB4E45EBA0D581", "decimals": 18},
    "P1": {"address": "0x44369AAFDD04CD9609A57EC0237884F45DD80818", "decimals": 18},
    "RBSD": {"address": "0x8A86D48C867B76FF74A36D3AF4D2F1E707B143ED", "decimals": 18},
    "RED": {"address": "0x92EAC40C98B383EA0F0EFDA747BDAC7AC891D300", "decimals": 18},
    "TFAT": {"address": "0x24D2FD6C5B29EEBD5169CC7D6E8014CD65DECD73", "decimals": 18},
    "USDX": {"address": "0xD875BA8E2CAD3C0F7E2973277C360C8D2F92B510", "decimals": 6},
    "USDm": {"address": "0xBDD352F339E27E07089039BA80029F9135F6146F", "decimals": 6},
    "WBTC": {"address": "0xCF5A6076CFA32686C0DF13ABADA2B40DEC133F1D", "decimals": 8},
    "WETH": {"address": "0xB5A30B0FDC5EA94A52FDC42E3E9760CB8449FB37", "decimals": 18},
    "WMON": {"address": "0x760AFE86E5DE5FA0EE542FC7B7B713E1C5425701", "decimals": 18},
    "WSOL": {"address": "0x5387C85A4965769F6B0DF430638A1388493486F1", "decimals": 9},
    "YAKI": {"address": "0xFE140E1DCE99BE9F4F15D657CD9B7BF622270C50", "decimals": 18},
    "aprMON": {"address": "0xB2F82D0F38DC453D596AD40A37799446CC89274A", "decimals": 18},
    "gMON": {"address": "0xAEEF2F6B429CB59C9B2D7BB2141ADA993E8571C3", "decimals": 18},
    "iceMON": {"address": "0xCEB564775415B524640D9F688278490A7F3EF9CD", "decimals": 18},
    "mamaBTC": {"address": "0x3B428DF09C3508D884C30266AC1577F099313CF6", "decimals": 8},
    "muBOND": {"address": "0x0EFED4D9FB7863CCC7BB392847C08DCD00FE9BE2", "decimals": 18},
    "sMON": {"address": "0xE1D2439B75FB9746E7BC6CB777AE10AA7F7EF9C5", "decimals": 18},
    "shMON": {"address": "0x3A98250F98DD388C211206983453837C8365BDC1", "decimals": 18},
    "stMON": {"address": "0x199C0DA6F291A897302300AAAE4F20D139162916", "decimals": 18}
}

ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]

WALLET_ABI = [
    {
        "inputs": [
            {"name": "recipient", "type": "address"},
            {"name": "token", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "sendTip",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "botAddress",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

FACTORY_ABI = [
    {
        "inputs": [
            {"name": "_botAddress", "type": "address"},
            {"name": "_owner", "type": "address"}
        ],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "inputs": [
            {"name": "fid", "type": "uint256"}
        ],
        "name": "createWallet",
        "outputs": [
            {"name": "", "type": "address"}
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "fid", "type": "uint256"}
        ],
        "name": "getWallet",
        "outputs": [
            {"name": "", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "wallet", "type": "address"}
        ],
        "name": "getFid",
        "outputs": [
            {"name": "", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "fid", "type": "uint256"}
        ],
        "name": "walletExists",
        "outputs": [
            {"name": "", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# ============================================================================
# Utility Functions
# ============================================================================
def ensure_checksum_address(address: str) -> str:
    try:
        return w3.to_checksum_address(address)
    except Exception as e:
        logger.error(f"Error converting address to checksum: {str(e)}")
        raise

def get_tip_bot_private_key():
    private_key = TIP_BOT_PRIVATE_KEY
    if not private_key:
        raise ValueError("TIP_BOT_PRIVATE_KEY not found in environment variables")
    if private_key.startswith('0x'):
        private_key = private_key[2:]
    if len(private_key) != 64:
        raise ValueError(f"Invalid private key length: {len(private_key)}. Expected 64 characters.")
    try:
        int(private_key, 16)
    except ValueError:
        raise ValueError("Private key contains invalid hexadecimal characters")
    return private_key

async def store_tip_details(
    tx_hash: str,
    tx_status: str,
    tipper_fid: str,
    tipper_username: str,
    tipper_wallet: str,
    recipient_fid: str,
    recipient_username: str,
    recipient_wallet: str,
    token_symbol: str,
    token_address: str,
    amount: float,
    amount_wei: int,  # Keep parameter for compatibility but don't store
    cast_hash: str,
    parent_cast_hash: str,
    block_number: int,
    gas_used: int,
    cast_timestamp: str,
    failure_reason: Optional[str] = None
):
    try:
        data = {
            "tx_hash": tx_hash,
            "tx_status": tx_status,
            "timestamp": cast_timestamp,
            "tipper_fid": int(tipper_fid) if tipper_fid else None,
            "tipper_username": tipper_username or "unknown",
            "tipper_wallet": tipper_wallet,
            "recipient_fid": int(recipient_fid) if recipient_fid else None,
            "recipient_username": recipient_username or "unknown",
            "recipient_wallet": recipient_wallet,
            "token_symbol": token_symbol,
            "token_address": token_address,
            "amount": amount,
            # Removed amount_wei from database storage to prevent bigint overflow
            "cast_hash": cast_hash,
            "parent_cast_hash": parent_cast_hash,
            "block_number": block_number,
            "gas_used": gas_used,
            "failure_reason": failure_reason
        }
        response = supabase.table("tip_transactions").insert(data).execute()
        logger.info(f"Stored tip details in Supabase: {response.data}")
    except Exception as e:
        logger.error(f"Error storing tip details in Supabase: {str(e)}")

# ============================================================================
# Farcaster API Functions
# ============================================================================
async def fetch_parent_cast(parent_hash: str) -> Dict:
    url = f"https://api.neynar.com/v2/farcaster/cast?identifier={parent_hash}&type=hash"
    headers = {"x-api-key": NEYNAR_API_KEY}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json().get("cast", {})

# ============================================================================
# Tip Processing Functions
# ============================================================================
async def parse_tip_command(text: str) -> Optional[Tuple[str, float, str]]:
    # Allow !montip anywhere, and 'tip' is optional
    parts = text.lower().split()
    if '!montip' not in parts:
        return None
    idx = parts.index('!montip')
    # Accept both '!montip tip' and '!montip' (tip optional)
    if len(parts) > idx + 1 and parts[idx + 1] == 'tip':
        idx += 1  # skip 'tip'
    # Now expect: !montip [tip] <amount> <token>
    try:
        amount = float(parts[idx + 1])
        token = parts[idx + 2].lstrip('$').upper()
        if token not in SUPPORTED_TOKENS:
            return None
        return '!montip', amount, token
    except (IndexError, ValueError):
        return None

async def process_tip_and_notify(
    cast: Dict,
    amount: float,
    token: str,
    tipper_fid: str,
    parent_hash: str,
    cast_hash: str,
    cast_timestamp: str,  # Add cast timestamp parameter
) -> None:
    try:
        # 1. Get parent cast and recipient info
        parent_cast = await fetch_parent_cast(parent_hash)
        recipient_fid = str(parent_cast["author"]["fid"])
        recipient_address = ensure_checksum_address(
            parent_cast["author"]["verified_addresses"]["primary"]["eth_address"]
        )
        # 2. Get tipper's wallet from factory
        factory = w3.eth.contract(address=ensure_checksum_address(FACTORY_ADDRESS), abi=FACTORY_ABI)
        tipper_wallet = factory.functions.getWallet(int(tipper_fid)).call()
        if tipper_wallet == "0x0000000000000000000000000000000000000000":
            logger.error(f"No smart wallet found for FID: {tipper_fid}")
            await store_tip_details(
                tx_hash="none",
                tx_status="failed",
                tipper_fid=tipper_fid,
                tipper_username=cast["author"].get("username", "unknown"),
                tipper_wallet="none",
                recipient_fid=recipient_fid,
                recipient_username=parent_cast["author"].get("username", "unknown"),
                recipient_wallet=recipient_address,
                token_symbol=token,
                token_address=SUPPORTED_TOKENS[token]["address"],
                amount=amount,
                amount_wei=int(amount * (10 ** SUPPORTED_TOKENS[token]["decimals"])),
                cast_hash=cast_hash,
                parent_cast_hash=parent_hash,
                block_number=0,
                gas_used=0,
                cast_timestamp=cast_timestamp,
                failure_reason="No smart wallet found for tipper"
            )
            return
        # 3. Get wallet contract
        wallet = w3.eth.contract(
            address=ensure_checksum_address(tipper_wallet),
            abi=WALLET_ABI
        )
        # 4. Check token support
        if token not in SUPPORTED_TOKENS:
            await store_tip_details(
                tx_hash="none",
                tx_status="failed",
                tipper_fid=tipper_fid,
                tipper_username=cast["author"].get("username", "unknown"),
                tipper_wallet=tipper_wallet,
                recipient_fid=recipient_fid,
                recipient_username=parent_cast["author"].get("username", "unknown"),
                recipient_wallet=recipient_address,
                token_symbol=token,
                token_address="none",
                amount=amount,
                amount_wei=int(amount * (10 ** SUPPORTED_TOKENS[token]["decimals"])),
                cast_hash=cast_hash,
                parent_cast_hash=parent_hash,
                block_number=0,
                gas_used=0,
                cast_timestamp=cast_timestamp,
                failure_reason="Unsupported token"
            )
            return
        # 5. Convert addresses to checksum format
        try:
            recipient_address = ensure_checksum_address(recipient_address)
            smart_wallet = ensure_checksum_address(tipper_wallet)
        except Exception as e:
            logger.error(f"Error converting addresses: {str(e)}")
            await store_tip_details(
                tx_hash="none",
                tx_status="failed",
                tipper_fid=tipper_fid,
                tipper_username=cast["author"].get("username", "unknown"),
                tipper_wallet=tipper_wallet,
                recipient_fid=recipient_fid,
                recipient_username=parent_cast["author"].get("username", "unknown"),
                recipient_wallet=recipient_address,
                token_symbol=token,
                token_address=SUPPORTED_TOKENS[token]["address"],
                amount=amount,
                amount_wei=int(amount * (10 ** SUPPORTED_TOKENS[token]["decimals"])),
                cast_hash=cast_hash,
                parent_cast_hash=parent_hash,
                block_number=0,
                gas_used=0,
                cast_timestamp=cast_timestamp,
                failure_reason=f"Invalid address format: {str(e)}"
            )
            return
        # 6. Verify smart wallet
        if smart_wallet == "0x0000000000000000000000000000000000000000":
            await store_tip_details(
                tx_hash="none",
                tx_status="failed",
                tipper_fid=tipper_fid,
                tipper_username=cast["author"].get("username", "unknown"),
                tipper_wallet=smart_wallet,
                recipient_fid=recipient_fid,
                recipient_username=parent_cast["author"].get("username", "unknown"),
                recipient_wallet=recipient_address,
                token_symbol=token,
                token_address=SUPPORTED_TOKENS[token]["address"],
                amount=amount,
                amount_wei=int(amount * (10 ** SUPPORTED_TOKENS[token]["decimals"])),
                cast_hash=cast_hash,
                parent_cast_hash=parent_hash,
                block_number=0,
                gas_used=0,
                cast_timestamp=cast_timestamp,
                failure_reason="Smart wallet not created"
            )
            return
        # 7. Process token transfer
        token_info = SUPPORTED_TOKENS[token]
        token_address = ensure_checksum_address(token_info["address"]) if token != "MON" else "0x0000000000000000000000000000000000000000"
        decimals = token_info["decimals"]
        amount_wei = int(amount * (10 ** decimals))
        try:
            wallet_contract = w3.eth.contract(address=smart_wallet, abi=WALLET_ABI)
            private_key = get_tip_bot_private_key()
            account = Account.from_key(private_key)
            bot_address = account.address
            contract_bot_address = wallet_contract.functions.botAddress().call()
            if contract_bot_address.lower() != bot_address.lower():
                logger.error(f"Bot address {bot_address} not authorized for smart wallet {smart_wallet}")
                await store_tip_details(
                    tx_hash="none",
                    tx_status="failed",
                    tipper_fid=tipper_fid,
                    tipper_username=cast["author"].get("username", "unknown"),
                    tipper_wallet=smart_wallet,
                    recipient_fid=recipient_fid,
                    recipient_username=parent_cast["author"].get("username", "unknown"),
                    recipient_wallet=recipient_address,
                    token_symbol=token,
                    token_address=token_address,
                    amount=amount,
                    amount_wei=amount_wei,
                    cast_hash=cast_hash,
                    parent_cast_hash=parent_hash,
                    block_number=0,
                    gas_used=0,
                    cast_timestamp=cast_timestamp,
                    failure_reason="Bot not authorized for wallet"
                )
                return
            if token == "MON":
                balance = w3.eth.get_balance(smart_wallet)
                if balance < amount_wei:
                    await store_tip_details(
                        tx_hash="none",
                        tx_status="failed",
                        tipper_fid=tipper_fid,
                        tipper_username=cast["author"].get("username", "unknown"),
                        tipper_wallet=smart_wallet,
                        recipient_fid=recipient_fid,
                        recipient_username=parent_cast["author"].get("username", "unknown"),
                        recipient_wallet=recipient_address,
                        token_symbol=token,
                        token_address=token_address,
                        amount=amount,
                        amount_wei=amount_wei,
                        cast_hash=cast_hash,
                        parent_cast_hash=parent_hash,
                        block_number=0,
                        gas_used=0,
                        cast_timestamp=cast_timestamp,
                        failure_reason="Insufficient MON balance"
                    )
                    return
            else:
                token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
                balance = token_contract.functions.balanceOf(smart_wallet).call()
                if balance < amount_wei:
                    await store_tip_details(
                        tx_hash="none",
                        tx_status="failed",
                        tipper_fid=tipper_fid,
                        tipper_username=cast["author"].get("username", "unknown"),
                        tipper_wallet=smart_wallet,
                        recipient_fid=recipient_fid,
                        recipient_username=parent_cast["author"].get("username", "unknown"),
                        recipient_wallet=recipient_address,
                        token_symbol=token,
                        token_address=token_address,
                        amount=amount,
                        amount_wei=amount_wei,
                        cast_hash=cast_hash,
                        parent_cast_hash=parent_hash,
                        block_number=0,
                        gas_used=0,
                        cast_timestamp=cast_timestamp,
                        failure_reason=f"Insufficient {token} balance"
                    )
                    return
            try:
                gas = wallet_contract.functions.sendTip(
                    recipient_address, token_address, amount_wei
                ).estimate_gas({'from': bot_address})
            except Exception as e:
                logger.error(f"Gas estimation failed: {str(e)}")
                await store_tip_details(
                    tx_hash="none",
                    tx_status="failed",
                    tipper_fid=tipper_fid,
                    tipper_username=cast["author"].get("username", "unknown"),
                    tipper_wallet=smart_wallet,
                    recipient_fid=recipient_fid,
                    recipient_username=parent_cast["author"].get("username", "unknown"),
                    recipient_wallet=recipient_address,
                    token_symbol=token,
                    token_address=token_address,
                    amount=amount,
                    amount_wei=amount_wei,
                    cast_hash=cast_hash,
                    parent_cast_hash=parent_hash,
                    block_number=0,
                    gas_used=0,
                    cast_timestamp=cast_timestamp,
                    failure_reason=f"Gas estimation failed: {str(e)}"
                )
                return
            tx = wallet_contract.functions.sendTip(
                recipient_address,
                token_address,
                amount_wei
            ).build_transaction({
                'from': bot_address,
                'gas': gas,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(bot_address),
                'chainId': 10143
            })
            signed_tx = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            try:
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                if receipt.status == 1:
                    logger.info(f"Transaction confirmed: {tx_hash.hex()}")
                else:
                    logger.error(f"Transaction failed: {tx_hash.hex()}")
                    await store_tip_details(
                        tx_hash=tx_hash.hex(),
                        tx_status="failed",
                        tipper_fid=tipper_fid,
                        tipper_username=cast["author"].get("username", "unknown"),
                        tipper_wallet=smart_wallet,
                        recipient_fid=recipient_fid,
                        recipient_username=parent_cast["author"].get("username", "unknown"),
                        recipient_wallet=recipient_address,
                        token_symbol=token,
                        token_address=token_address,
                        amount=amount,
                        amount_wei=amount_wei,
                        cast_hash=cast_hash,
                        parent_cast_hash=parent_hash,
                        block_number=receipt.blockNumber,
                        gas_used=receipt.gasUsed,
                        cast_timestamp=cast_timestamp,
                        failure_reason="Transaction reverted"
                    )
                    return
            except Exception as e:
                logger.error(f"Transaction confirmation failed: {str(e)}")
                await store_tip_details(
                    tx_hash=tx_hash.hex() if 'tx_hash' in locals() else "none",
                    tx_status="failed",
                    tipper_fid=tipper_fid,
                    tipper_username=cast["author"].get("username", "unknown"),
                    tipper_wallet=smart_wallet,
                    recipient_fid=recipient_fid,
                    recipient_username=parent_cast["author"].get("username", "unknown"),
                    recipient_wallet=recipient_address,
                    token_symbol=token,
                    token_address=token_address,
                    amount=amount,
                    amount_wei=amount_wei,
                    cast_hash=cast_hash,
                    parent_cast_hash=parent_hash,
                    block_number=0,
                    gas_used=gas if 'gas' in locals() else 0,
                    cast_timestamp=cast_timestamp,
                    failure_reason=f"Transaction confirmation failed: {str(e)}"
                )
                return
            try:
                tipper_username = cast["author"].get("username", "unknown")
            except Exception:
                tipper_username = "unknown"
            try:
                recipient_username = parent_cast["author"].get("username", "unknown")
            except Exception:
                recipient_username = "unknown"
            await store_tip_details(
                tx_hash=tx_hash.hex(),
                tx_status="success",
                tipper_fid=tipper_fid,
                tipper_username=tipper_username,
                tipper_wallet=smart_wallet,
                recipient_fid=recipient_fid,
                recipient_username=recipient_username,
                recipient_wallet=recipient_address,
                token_symbol=token,
                token_address=token_address,
                amount=amount,
                amount_wei=amount_wei,
                cast_hash=cast_hash,
                parent_cast_hash=parent_hash,
                block_number=receipt.blockNumber,
                gas_used=receipt.gasUsed,
                cast_timestamp=cast_timestamp,
                failure_reason=None
            )
        except ValueError as e:
            logger.error(f"Error sending transaction: {str(e)}")
            await store_tip_details(
                tx_hash="none",
                tx_status="failed",
                tipper_fid=tipper_fid,
                tipper_username=cast["author"].get("username", "unknown"),
                tipper_wallet=smart_wallet,
                recipient_fid=recipient_fid,
                recipient_username=parent_cast["author"].get("username", "unknown"),
                recipient_wallet=recipient_address,
                token_symbol=token,
                token_address=token_address,
                amount=amount,
                amount_wei=amount_wei,
                cast_hash=cast_hash,
                parent_cast_hash=parent_hash,
                block_number=0,
                gas_used=gas if 'gas' in locals() else 0,
                cast_timestamp=cast_timestamp,
                failure_reason=f"Transaction error: {str(e)}"
            )
            return
        except Exception as e:
            logger.error(f"Error processing tip: {str(e)}")
            await store_tip_details(
                tx_hash="none",
                tx_status="failed",
                tipper_fid=tipper_fid,
                tipper_username=cast["author"].get("username", "unknown"),
                tipper_wallet=smart_wallet,
                recipient_fid=recipient_fid,
                recipient_username=parent_cast["author"].get("username", "unknown"),
                recipient_wallet=recipient_address,
                token_symbol=token,
                token_address=token_address,
                amount=amount,
                amount_wei=amount_wei,
                cast_hash=cast_hash,
                parent_cast_hash=parent_hash,
                block_number=0,
                gas_used=gas if 'gas' in locals() else 0,
                cast_timestamp=cast_timestamp,
                failure_reason=f"Processing error: {str(e)}"
            )
            return
    except Exception as e:
        logger.error(f"Error processing tip: {str(e)}")
        await store_tip_details(
            tx_hash="none",
            tx_status="failed",
            tipper_fid=tipper_fid,
            tipper_username=cast["author"].get("username", "unknown"),
            tipper_wallet="none",
            recipient_fid=recipient_fid,
            recipient_username=parent_cast["author"].get("username", "unknown") if 'parent_cast' in locals() else "unknown",
            recipient_wallet=recipient_address if 'recipient_address' in locals() else "none",
            token_symbol=token,
            token_address=SUPPORTED_TOKENS[token]["address"] if token in SUPPORTED_TOKENS else "none",
            amount=amount,
            amount_wei=int(amount * (10 ** SUPPORTED_TOKENS[token]["decimals"])) if token in SUPPORTED_TOKENS else 0,
            cast_hash=cast_hash,
            parent_cast_hash=parent_hash,
            block_number=0,
            gas_used=0,
            cast_timestamp=cast_timestamp,
            failure_reason=f"General processing error: {str(e)}"
        )

# ============================================================================
# FastAPI App Setup
# ============================================================================
app = FastAPI()

@app.post("/webhook")
async def webhook_listener(request: Request, background_tasks: BackgroundTasks):
    """Handle incoming webhooks from Farcaster."""
    # --- Neynar Webhook Signature Verification ---
    signature = request.headers.get("X-Neynar-Signature")
    if not signature:
        logger.warning("Missing Neynar signature header")
        return {"error": "Missing signature"}, 400

    webhook_secret = os.getenv("NEYNAR_WEBHOOK_SECRET")
    body = await request.body()  # Get raw bytes, not JSON

    computed_sig = hmac.new(
        webhook_secret.encode(),
        body,
        hashlib.sha512
    ).hexdigest()

    if not hmac.compare_digest(computed_sig, signature):
        logger.warning("Invalid Neynar webhook signature")
        return {"error": "Invalid signature"}, 401

    # Now it's safe to parse the JSON
    try:
        data = await request.json()
        logger.info(f"Received webhook: {data}")
        if data.get("type") == "cast.created":
            cast = data.get("data", {})
            text = cast.get("text", "").lower()
            tipper_fid = cast.get("author", {}).get("fid")
            parent_hash = cast.get("parent_hash")
            cast_hash = cast.get("hash")
            cast_timestamp = cast.get("timestamp")  # Extract the cast timestamp
            # Only process if !montip is present and has a parent_hash
            is_command = '!montip' in text
            if not is_command or not parent_hash:
                logger.info(f"Cast ignored: Not a !montip command or not a reply. Text: {text}")
                return {"status": "ignored"}
            result = await parse_tip_command(text)
            if not result:
                logger.info(f"Invalid command: {text}")
                return {"status": "invalid_command"}
            _, amount, token = result
            background_tasks.add_task(
                process_tip_and_notify,
                cast=cast,
                amount=amount,
                token=token,
                tipper_fid=tipper_fid,
                parent_hash=parent_hash,
                cast_hash=cast_hash,
                cast_timestamp=cast_timestamp  # Pass the cast timestamp
            )
            return {"status": "processing"}
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {"error": str(e)}

# ============================================================================
# Main Entry Point
# ============================================================================
if __name__ == "__main__":
    # For local dev only; use Gunicorn/Uvicorn for production
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ============================================================================
# Tips for Running with Uvicorn and Gunicorn in Production
# ============================================================================
# 1. Uvicorn (standalone, good for dev or small prod):
#    uvicorn tip:app --host 0.0.0.0 --port 8000 --workers 4
#
# 2. Gunicorn (recommended for production, with Uvicorn workers):
#    gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 tip:app
#
#    -w 4 means 4 worker processes (adjust based on CPU cores)
#    -k uvicorn.workers.UvicornWorker tells Gunicorn to use Uvicorn for async
#    -b 0.0.0.0:8000 binds to all interfaces on port 8000
#
# 3. Use a process manager (like systemd or supervisor) to keep your server running
# 4. Always run behind a reverse proxy (like nginx) for SSL and security
# 5. Monitor logs and set up alerts for errors or high latency
#
# More: https://www.uvicorn.org/deployment/ and https://docs.gunicorn.org/en/stable/run.html
#
# Reference for Neynar signature: https://docs.neynar.com/docs/how-to-verify-the-incoming-webhooks-using-signatures
