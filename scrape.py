import asyncio
from discord.ext import tasks, commands
import requests
import discord

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

found_codes = {}  # Initialize found_codes as a dictionary
token = ""

async def scrape_codes():
    url = 'https://swq.jp/_special/rest/Sw/Coupon'
    params = {}
    response = requests.get(url, params=params)
    data = response.json()
    codes = []
    for coupon in data.get('data', []):
        status = coupon.get('Status')
        if status == "verified":  # Only include codes with status "verified"
            label = coupon.get('Label')
            resources = coupon.get('Resources', [])
            reward_info = ''
            for resource in resources:
                quantity = resource.get('Quantity')
                reward = resource.get('Sw_Resource', {}).get('Label_I18n')
                reward_info += f"{quantity} {reward}, "
            reward_info = reward_info.rstrip(', ')
            votes = coupon.get('Score')
            
            if "Mystical scroll" in reward_info:
                reward_info = reward_info.replace("Mystical scroll","<:mystical_scroll:1133230446096941147>")
                
            if "Light and dark scroll" in reward_info:
                reward_info = reward_info.replace("Light and dark scroll","<:dl_scroll:1133231377735745607>")
                
            if "Water scroll" in reward_info:
                reward_info = reward_info.replace("Water scroll","<:water_scroll:1133960672288456825>")

            if "Wind scroll" in reward_info:
                reward_info = reward_info.replace("Wind scroll","<:wind_scroll:1133232580746022942>")


            if "Fire scroll" in reward_info:
                reward_info = reward_info.replace("Fire scroll","<:fire_scroll:1133232350042525837>")
                
            if "Mana" in reward_info:
                reward_info = reward_info.replace("Mana","<:mana:1133231741121871872>")

            codes.append({
                'code': label,
                'reward': reward_info,
                'votes': votes
            })
    return codes


last_notification_message = None  # Pour garder une trace du dernier message de notification



last_codes_message = None  # Pour garder une trace du dernier message avec les codes

@tasks.loop(seconds=15)  # s'exécute toutes les 15 secondes
async def scrape_and_post():
    global found_codes, last_codes_message
    all_codes = await scrape_codes()

    new_code = None  # Pour garder une trace du nouveau code trouvé

    for code in all_codes:
        label = code['code']

        if label not in found_codes:
            # If the code is new, add it to the list and save it as new_code
            found_codes[label] = code
            new_code = code

    sorted_codes = sorted(found_codes.values(), key=lambda x: int(x['votes']), reverse=True)

    # Choose a specific guild to post the message in
    guild = bot.guilds[0]  # Change this to the guild you want

    channel = discord.utils.get(guild.text_channels, name="code-summoners-wars")
    if channel is None:
        channel = await guild.create_text_channel('code-summoners-wars')

    codes_info = '**Voici les codes trouvés :**\n'
    for code in sorted_codes:
        votes = int(code['votes'])
        if votes > 5:
            codes_info += f"Code: {code['code']}\nRécompense: {code['reward']}\nVote: {votes}\n\n"

    if new_code is not None:
        votes = int(new_code['votes'])
        if votes > 5:
            codes_info += f"**Un nouveau code a été ajouté!**\nCode: {new_code['code']}\nRécompense: {new_code['reward']}\nVote: {new_code['votes']}\n"
            if last_codes_message is not None:
                await last_codes_message.delete()  # delete the old message
            last_codes_message = await channel.send(codes_info)  # send a new message with all the codes
    else:
        if last_codes_message is not None:
            await last_codes_message.edit(content=codes_info)  # update the existing message with all the codes
        else:
            last_codes_message = await channel.send(codes_info)  # send a new message with all the codes if it doesn't exist



@bot.event
async def on_ready():
    print('Bot is ready.')
    scrape_and_post.start()

@bot.command()
async def showallcode(ctx):
    global found_codes
    if found_codes:
        sorted_codes = sorted(found_codes.values(), key=lambda x: int(x['votes']), reverse=True)
        all_code_info = ''
        for code in sorted_codes:
            all_code_info += f"Code: {code['code']}\nRécompense: {code['reward']}\nVote: {code['votes']}\n"
        await ctx.send("```" + all_code_info + "```")
    else:
        await ctx.send("Pas de nouveaux codes disponibles pour le moment.")

bot.run(token)
