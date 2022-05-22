from discord_components import ComponentsBot,Button, Select, SelectOption
from discord.ext import commands
import discord.embeds
import random
import json
import os
import time
from discord.gateway import DiscordWebSocket

configFile = open("config.json")
config = json.load(configFile)

client = ComponentsBot(command_prefix = config["prefix"])

def thousand_sep(num):
    return ("{:,}".format(num))

if config["phoneStatus"]:
    class MyDiscordWebSocket(DiscordWebSocket):
        async def send_as_json(self, data):
            if data.get('op') == self.IDENTIFY:
                if data.get('d', {}).get('properties', {}).get('$browser') is not None:
                    data['d']['properties']['$browser'] = 'Discord Android'
                    data['d']['properties']['$device'] = 'Discord Android'
            await super().send_as_json(data)


    DiscordWebSocket.from_client = MyDiscordWebSocket.from_client

@client.event
async def on_ready():
    print(f"Logged in as {client.user}!")
    await client.change_presence(activity=discord.Game(name="github.com/o0ent"))     


#Admin commands
@client.command(name="restock",descriprion="Restock product")
@commands.guild_only()
@commands.has_permissions(administrator = True)
async def reStock(ctx, arg):
    filePath = f"accounts/{arg}.txt"
    for attachment in ctx.message.attachments:
        await attachment.save(attachment.filename)
        fileStock = open(attachment.filename,"r")
        toStock = open(filePath,"a")
        for line in fileStock:
            toStock.write(line)
        toStock.write("\n")

        fileStock.close()
        
    time.sleep(0.5)
    os.remove(attachment.filename)

    await ctx.send("Successfully restocked!")

@client.command(name="create")
@commands.guild_only()
@commands.has_permissions(administrator = True)
async def createStock(ctx, arg):
    filePath = f"accounts/{arg}.txt"
    try:
        productName = open(filePath, 'r')
        await ctx.send(f"Product already exsist!")
    except IOError:
        productName = open(filePath, 'w')
        await ctx.send(f"Created product with name **{arg}**")

@client.command(name="dump")
@commands.guild_only()
@commands.has_permissions(administrator = True)
async def dumpStock(ctx):
        dir_list = os.listdir("accounts")
        productsList = []
        for i in dir_list:
            line_count = 0
            totalAccs = open(f"accounts/{i}","r")
            prodName = i.split(".txt")[0]
            productsList.append(SelectOption(label = prodName, value = prodName,description=f"{thousand_sep(len(totalAccs.readlines()))} accounts"))
        await ctx.send(
            "Select product to dump",
            components = [
                Select(
                    placeholder = "Dump",
                    options = productsList
                )
            ]
        )

        interaction = await client.wait_for("select_option")
        filePath = f"accounts/{interaction.values[0]}.txt"
        await interaction.send(file=discord.File(filePath))

#Users commands
@client.command(name="gen",descriprion="Generates account")
@commands.guild_only()
async def genStock(ctx):
    if ctx.channel.id == config["channelId"]:
        dir_list = os.listdir("accounts")
        productsList = []
        for i in dir_list:
            line_count = 0
            totalAccs = open(f"accounts/{i}","r")
            prodName = i.split(".txt")[0]
            productsList.append(SelectOption(label = prodName, value = prodName,description=f"{thousand_sep(len(totalAccs.readlines()))} accounts"))
        await ctx.send(
            "Hello, welcome to Verto Alts, if you want to generate a product, below you can select your favorite product and it will automatically send you a PM.",
            components = [
                Select(
                    placeholder = "Select product",
                    options = productsList
                )
            ]
        )

        interaction = await client.wait_for("select_option")
        filePath = f"accounts/{interaction.values[0]}.txt"
        try:
            rows = open(filePath,"r").readlines()
            random_line_number = random.randint(0, len(rows) - 1)
            for i in range(config["accountstoGen"]):
                random_line_content = rows.pop(random_line_number)
                user = await client.fetch_user(ctx.author.id)
                # await user.send(random_line_content)
                embed=discord.Embed(title="VertoAlts | Account", description=f"Your account for {interaction.values[0]}")
                embed.add_field(name="Thank you for using our service", value=f"```{random_line_content}```", inline=True)
                embed.set_footer(text=f"generated by {ctx.author.name}#{ctx.author.discriminator}")

                embed1=discord.Embed(title="VertoAlts | Generated", description=f"{ctx.author.mention} just generated account for {interaction.values[0]}")
                # await user.send(embed=embed)
                await interaction.send(embed=embed)
                await ctx.send(embed=embed1)

                if config["deleteAccsfromDB"]:
                    with open(filePath, "r+") as f:
                        d = f.readlines()
                        f.seek(0)
                        for i in d:
                            if i != random_line_content:
                                f.write(i)
                        f.truncate()        
        except ValueError:
            embed=discord.Embed(title="VertoAlts | Error",description = 'Product is out of stock, generate another one', color=0xdd0000)
            await interaction.send(embed=embed)
        except FileNotFoundError:
            embed=discord.Embed(title="VertoAlts | Error",description = "Can't find product!", color=0xdd0000)
            await interaction.send(embed=embed)
    else:
        embed=discord.Embed(title="VertoAlts | Error",description = "You can't use commands in this channel", color=0xdd0000)
        await interaction.send(embed=embed)

@client.command(name="stats",descriprion="Status")
async def getStock(ctx):
    dir_list = os.listdir("accounts")
    embed=discord.Embed(title="VertoAlts | Statistic", description=f"We have a {len(dir_list)} products",color=0x999999)
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/956494913732743218/977163622017036318/White_Colorful_Modern_Gradient_Play_Media_Logo.png")
    for i in dir_list:
        line_count = 0
        totalAccs = open(f"accounts/{i}","r")
        embed.add_field(name=i.split(".txt")[0], value=thousand_sep(len(totalAccs.readlines())), inline=True)
    
    embed.set_footer(text=f"requested by {ctx.author.name}#{ctx.author.discriminator}")
    await ctx.send(embed=embed)


client.run(config["token"])