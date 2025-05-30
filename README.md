# Farcaster TipBot Backend

A powerful and social tipping bot for the Farcaster ecosystem that enables users to send tips on Monad Testnet, track transactions, and engage with the community through social features.

## Features

- 💸 Real-time tipping functionality with multiple token support
- 🔄 Transaction tracking and history
- 🤖 Automated responses and notifications through Farcaster
- 🔗 Farcaster social integration via Neynar API
- 🔐 Secure webhook handling
- 💼 Smart contract wallet management
- 📈 Performance monitoring with async logging

## Prerequisites

- Python 3.8+
- Neynar API access
- Monad Testnet RPC access
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:

git clone [your-repo-url]
cd montipbot
```

2. Install dependencies:

pip install -r requirements.txt
```

3. Set up environment variables:

## Configuration

Create a `.env` file with the following variables:
```
MONAD_TESTNET_RPC_URL=your_rpc_url
BOT_USERNAME=your_bot_username
BOT_FID=your_bot_fid
NEYNAR_API_KEY=your_neynar_api_key
NEYNAR_WEBHOOK_SECRET=your_webhook_secret
NEYNAR_SIGNER_UUID=your_signer_uuid
FACTORY_ADDRESS=your_factory_contract_address
TIP_BOT_PRIVATE_KEY=your_private_key
TIP_BOT_ADDRESS=your_bot_address
DEPLOYER_PRIVATE_KEY=your_deployer_private_key
OWNER_PRIVATE_KEY=your_owner_private_key
OWNER_ADDRESS=your_owner_address
```

## Usage

1. Start the bot:

uvicorn tip:app --host 0.0.0.0 --port 8000
```

2. Monitor logs:

tail -f bot.log
```

## Supported Tokens

The bot supports multiple tokens on Monad Testnet:
- MON (Native token)
- USDC, USDT
- Various community tokens (BEAN, BMONAD, CHOG, etc.)
- Wrapped tokens (WBTC, WETH, WSOL)
- And many more (see SUPPORTED_TOKENS in tip.py)

## Bot Commands

- `!montip tip <amount> <token>` - Send a tip to a user
Example: `!montip tip 1 MON`

## Development

### Project Structure
```
tipbot/
├── tip.py              # Main bot file
├── requirements.txt    # Python dependencies
├── bot.log            # Log file
└── .env               # Environment configuration
```

### Adding New Features

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Submit a pull request

or 

1. Implement changes directly in tip.py 

## Security Features

- HMAC signature verification for webhooks
- Secure private key handling
- Input validation and sanitization
- Asynchronous logging for errors and warnings

## Contributing

We welcome contributions! Please read our contributing guidelines before submitting pull requests.

## Support

For support, please open an issue in the repository.
