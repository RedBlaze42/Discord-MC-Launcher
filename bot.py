import discord
import os
import json
from time import time
from asyncio import sleep

bot=discord.Client()
with open("config.json","r") as file:
    config=json.load(file)

minecraft_names=["Minecraft"]
time_to_stop=0

def cmdFile(cmd):
	os.system(str(cmd)+">tmp 2>&1")
	with open('tmp',"r") as file:
		data=file.read().split("\n")
	os.remove("tmp")
	return data

def launch_server():
    cmd="screen -dmS mc_server "+config["server_executable"]
    print(cmd)
    os.system(cmd)

def send_mc_message(msg):
    os.system('screen -S mc_server -p 0 -X mc_server "say {}^M"'.format(msg))

def stop_server():
    os.system('screen -S mc_server -p 0 -X mc_server "stop^M"')

def save_config():
    with open("config.json","w") as file:
        json.dump(config,file)

def is_playing(member):
    games=[activity.name for activity in member.activities if isinstance(activity,discord.Game)]
    for name in minecraft_names:
        if name in games: return True

    return False

def list_players(members):
    return [member for member in members if is_playing(member)]

def count_players(members):
    return len(list_players(members))

def is_server_running():
    return "mc_server" in cmdFile("screen -ls")

@bot.event
async def on_member_update(before,after):
    if(config["member_role"]==0 or config["notification_channel"]==0):
        await before.guild.channels[0].send("You need configure your bot using !mine config")
        return False
    guild=before.guild
    members=guild.get_role(config["member_role"]).members
    channel=guild.get_channel(config["notification_channel"])

    server_on=is_server_running()
    if(count_players(members)<config["minimum_connected"] and server_on):
        if time_to_stop==0:
            
            time_to_stop=config["treshold"]+time()
            while(time()<time_to_stop and count_players(members)<config["minimum_connected"]):
                sleep(5)

            if count_players(members)<config["minimum_connected"]:
                send_mc_message("Arrêt du serveur")
                sleep(5)
                stop_server()
                channel.send("Serveur arrêté")
            else:
                send_mc_message("Arrêt annulé")
        else:
            return None
    elif(count_players(members)>=config["minimum_connected"] and not server_on):
        launch_server()
        time_to_stop==0
        channel.send("Lancement du serveur par "+" ".join(["<@{}>".format(str(player.id)) for player in list_players()]))

@bot.event
async def on_message(message):
    if message.content.startswith("!mine") and message.author.guild_permissions.administrator and not message.author.bot:
        if not config["member_role"]==0:
            role="@"+message.channel.guild.get_role(config["member_role"]).name
        else:
            role="nothing"
        args=message.content.split(" ")[1:]

        if len(args)==0:
            message.channel.send("Tapez !mine help pour l'aide")
        elif args[0] == "setchannel":
            config["notification_channel"]=message.channel.id
            save_config()
            await message.channel.send("Notification channel set to <#{}>".format(str(message.channel.id)))
        elif args[0]=="treshold" and len(args)>1:
            config["treshold"]=int(args[1])
            save_config()
            await message.channel.send("Treshold set to `{}`".format(config["members_count"]))
        elif args[0]=="role" and len(message.role_mentions)==1:
            config["member_role"]=message.role_mentions[0].id
            save_config()
            await message.channel.send("Role set to @{}".format(message.role_mentions[0].name))
        elif args[0]=="server" and len(args)>1:
            config["server_executable"]=" ".join(args[1:])
            save_config()
            await message.channel.send("Server executable set to `{}`".format(config["server_executable"]))
        elif args[0]=="members_count" and len(args)>1:
            config["minimum_connected"]=int(args[1])
            save_config()
            await message.channel.send("Minimum members connected set to `{}`".format(config["minimum_connected"]))
        else:
            embed=discord.Embed(title="Minecraft launcher bot config",colour=discord.Colour(0x0000))
            embed.description="""**!mine setchannel** to set the notification channel, currently set to: <#{channel}>
            **!mine treshold** to set the treshold in seconds, currently set to: `{treshold}s`
            **!mine members_count** to set minimum members connected, currently set to: `{members}`
            **!mine role** to set the minecraft players role (you need to mention it), currently set to: `{role}`
            **!mine server** to set server launch command, currently set to: `{command}`""".format(
                treshold=config["treshold"],
                members=config["minimum_connected"],
                command=config["server_executable"],
                channel=config["notification_channel"],
                role=role)
            embed.set_footer(text="Bot made by RedBlaze#0645")
            await message.channel.send(embed=embed)

bot.run(config["token"])