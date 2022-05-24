from discord.gateway import DiscordWebSocket
from discord.ext.commands import cooldown,BucketType
from discord.ui import Select,View
from discord import app_commands
from discord import ui
import discord
import random
import json
import time
import os

from requests import options


configFile = open("config.json")
config = json.load(configFile)

class client(discord.Client):
    def __init__(self):
        super().__init__(intents = discord.Intents.default())
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync(guild = discord.Object(id=config["serverId"]))
            self.synced = True
        print(f"Logged in as {self.user}.")
        await self.change_presence(activity=discord.Game(name="github.com/o0ent"))     

if config["phoneStatus"]:
    class MyDiscordWebSocket(DiscordWebSocket):
        async def send_as_json(self, data):
            if data.get('op') == self.IDENTIFY:
                if data.get('d', {}).get('properties', {}).get('$browser') is not None:
                    data['d']['properties']['$browser'] = 'Discord Android'
                    data['d']['properties']['$device'] = 'Discord Android'
            await super().send_as_json(data)


    DiscordWebSocket.from_client = MyDiscordWebSocket.from_client

aclient = client()

tree = app_commands.CommandTree(aclient)

class reStock(ui.Modal, title='Restock product'):
    name = ui.TextInput(label='Product')
    answer = ui.TextInput(label="Accounts (don't make empty lines!)", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            filePath = f"accounts/{self.name}.txt"
            cache = f'ACCOUNTS_{self.name}.txt'
            writed = open(cache,"w")
            writed.write(str(self.answer))
            writed.close()
            accounts = open(cache,"r")
            toStock = open(filePath,"a")

            for line in accounts:
                toStock.write(line.replace('\n\n','\n'))
            toStock.write("\n")
            accounts.close()
            time.sleep(0.5)
            os.remove(cache)

            await interaction.response.send_message("Successfully restocked!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(e, ephemeral=True)


class deleteType(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label='Delete product', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()

    @discord.ui.button(label='Delete accounts', style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()

def thousand_sep(num):
    return ("{:,}".format(num))

#Admin commands

@tree.command(guild = discord.Object(id=config["serverId"]), name = 'restock', description='Restocks accounts') #guild specific slash command
async def sendStock(interaction: discord.Interaction):
    if any(role.id in config["restockerRole"] for role in interaction.user.roles):
        await interaction.response.send_modal(reStock())
    else:
        embed=discord.Embed(title="VertoAlts | Error",description = 'Access denied', color=0xdd0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(guild = discord.Object(id=config["serverId"]), name = 'create', description='Create a new product') #guild specific slash command
async def createStock(interaction: discord.Interaction,name:str):
    if any(role.id in config["restockerRole"] for role in interaction.user.roles):
        filePath = f"accounts/{name}.txt"
        try:
            productName = open(filePath, 'r')
            await interaction.response.send_message(f"Product already exsist!", ephemeral=True)
        except IOError:
            productName = open(filePath, 'w')
            await interaction.response.send_message(f"Created product with name **{name}**", ephemeral=True)
    else:
        embed=discord.Embed(title="VertoAlts | Error",description = 'Access denied', color=0xdd0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(guild = discord.Object(id=config["serverId"]), name = 'delete', description='Deletes product/accounts') #guild specific slash command
async def deleteStock(interaction: discord.Interaction):
    if any(role.id in config["restockerRole"] for role in interaction.user.roles):
        dir_list = os.listdir("accounts")
        productsList = []
        for i in dir_list:
            totalAccs = open(f"accounts/{i}","r")
            prodName = i.split(".txt")[0]
            productsList.append(discord.SelectOption(label = prodName,description=f"{thousand_sep(len(totalAccs.readlines()))} accounts"))
            totalAccs.close()    

        select = Select(options=productsList)
        author = interaction.user

        async def delProd(interaction):
            if author == interaction.user:
                productSelected = select.values[0]
                filePath = f"accounts/{productSelected}.txt"
                try:
                    view = deleteType()
                    await interaction.response.edit_message(view=view)
                    # await interaction.response.send_message('Select', view=view,ephemeral = True)
                    await view.wait()
                    if view.value is None:
                        print('Timed out...')
                    elif view.value:
                        os.remove(filePath)
                        await interaction.followup.send('Product deleted',ephemeral = True)
                    else:
                        open(filePath, 'w').close()
                        await interaction.followup.send('Accounts deleted',ephemeral = True)


                except Exception as e:
                    print(e)
            else:
                embed=discord.Embed(title="VertoAlts | Error",description = "You can't generate an account because you are not the author of the message", color=0xdd0000)
                await interaction.response.send_message(embed=embed,ephemeral = True)
        select.callback = delProd

        view = View()
        view.add_item(select)
        await interaction.response.send_message(view=view,ephemeral = True) 


@tree.command(guild = discord.Object(id=config["serverId"]), name = 'dump', description='Get all accounts from product') #guild specific slash command
async def dumpStock(interaction: discord.Interaction,name:str):
    if any(role.id in config["restockerRole"] for role in interaction.user.roles):
        try:
            filePath = f"accounts/{name}.txt"
            await interaction.response.send_message(file=discord.File(filePath),ephemeral = True)
        except FileNotFoundError:
            embed=discord.Embed(title="VertoAlts | Error",description = "Can't find the product", color=0xdd0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed=discord.Embed(title="VertoAlts | Error",description = 'Access denied', color=0xdd0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)


#Users commands
@tree.command(guild = discord.Object(id=config["serverId"]), name = 'generate', description='Generate account') #guild specific slash command
async def genStock(interaction: discord.Interaction):
    dir_list = os.listdir("accounts")
    productsList = []
    for i in dir_list:
        totalAccs = open(f"accounts/{i}","r")
        prodName = i.split(".txt")[0]
        productsList.append(discord.SelectOption(label = prodName,description=f"{thousand_sep(len(totalAccs.readlines()))} accounts"))
        totalAccs.close()    
    select = Select(options=productsList)
    author = interaction.user
    async def getAcc(interaction):
        if interaction.channel.id == config["channelId"]:
            if author == interaction.user:
                try:
                    select.disabled = True
                    filePath = f"accounts/{select.values[0]}.txt"
                    random_line_content = random.choice(open(filePath).readlines())
                    embed=discord.Embed(title="VertoAlts | Account", description=f"Your account for {select.values[0]}")
                    embed.add_field(name="Thank you for using our service", value=f"```{random_line_content}```", inline=True)
                    embed.set_footer(text=f"generated by {author}")
                    embed1=discord.Embed(title="VertoAlts | Generated", description=f"{interaction.user.mention} just generated account for {select.values[0]}")

                    await interaction.response.edit_message(view=view)
                    await interaction.followup.send(embed=embed, ephemeral = True)
                    await interaction.followup.send(embed=embed1)

                    if config["deleteAccsfromDB"]:
                        with open(filePath, "r+") as f:
                            d = f.readlines()
                            f.seek(0)
                            for i in d:
                                if i != random_line_content:
                                    f.write(i)
                            f.truncate()
                except IndexError:
                    embed=discord.Embed(title="VertoAlts | Error",description = 'Product is out of stock, generate another one', color=0xdd0000)
                    await interaction.response.send_message(embed=embed,ephemeral = True)
                except FileNotFoundError:
                    embed=discord.Embed(title="VertoAlts | Error",description = "Can't find product!", color=0xdd0000)
                    await interaction.response.send_message(embed=embed,ephemeral = True)
            else:
                embed=discord.Embed(title="VertoAlts | Error",description = "You can't generate an account because you are not the author of the message", color=0xdd0000)
                await interaction.response.send_message(embed=embed,ephemeral = True)
        else:
                select.disabled = True
                embed=discord.Embed(title="VertoAlts | Error",description = "You can't use commands in this channel", color=0xdd0000)
                await interaction.response.edit_message(view=view)
                await interaction.followup.send(embed=embed, ephemeral = True)

    select.callback = getAcc

    view = View()
    view.add_item(select)

    await interaction.response.send_message("Hello, welcome to Verto Alts, if you want to generate a product, below you can select your favorite product and it will automatically send you a PM.",view=view) 

@tree.command(guild = discord.Object(id=config["serverId"]), name = 'stats', description='Show statistics about our products') #guild specific slash command
async def getStock(interaction: discord.Interaction):
    dir_list = os.listdir("accounts")
    embed=discord.Embed(title="VertoAlts | Statistic", description=f"We have a {len(dir_list)} products",color=0x999999)
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/956494913732743218/977163622017036318/White_Colorful_Modern_Gradient_Play_Media_Logo.png")
    for i in dir_list:
        totalAccs = open(f"accounts/{i}","r")
        embed.add_field(name=i.split(".txt")[0], value=thousand_sep(len(totalAccs.readlines())), inline=True)
        totalAccs.close()
    embed.set_footer(text=f"requested by {interaction.user}")
    await interaction.response.send_message(embed=embed)

@tree.command(guild = discord.Object(id=config["serverId"]), name = 'help', description='Shows commands') #guild specific slash command
async def getHelp(interaction: discord.Interaction):
    embed=discord.Embed(title="VertoAlts | Help", description=f"Help me please!",color=0x999999)
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/956494913732743218/977163622017036318/White_Colorful_Modern_Gradient_Play_Media_Logo.png")

    embed.add_field(name=f"Right now i can't make help command. Sorry", value="please", inline=True)
    embed.set_footer(text=f"requested by {interaction.user}")
    await interaction.response.send_message(embed=embed)

aclient.run(config["token"])