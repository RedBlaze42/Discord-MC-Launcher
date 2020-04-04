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
screen_name="mc_server_"+config["token"][:4]

def cmdFile(cmd):
	os.system(str(cmd)+">tmp 2>&1")
	with open('tmp',"r") as file:
		data=file.read().split("\n")
	os.remove("tmp")
	return data

def launch_server():
    if not is_server_running():
        cmd='screen -S {} -dm  bash -c "{}"'.format(screen_name,config["server_executable"])
        print(cmd)
        os.system(cmd)

def send_mc_message(msg):
    os.system('screen -S {} -X stuff "say {}^M"'.format(screen_name,msg))

def stop_server():
    if is_server_running(): os.system('screen -S {} -X stuff "stop^M"'.format(screen_name))

def save_config():
    with open("config.json","w") as file:
        json.dump(config,file)

def is_playing(member):
    games=[activity.name for activity in member.activities]
    for name in minecraft_names:
        if name in games: return True

    return False

def list_players(members):
    return [member for member in members if is_playing(member)]

def count_players(members):
    return len(list_players(members))

def is_server_running():
    return screen_name in "\n".join(cmdFile("screen -ls"))

def is_in_lock():
    return os.path.exists("treshold.lock")

def set_lock():
    with open("treshold.lock","w") as lock:
        lock.write(str(time()+config["treshold"]))

def remove_lock():
    if is_in_lock(): os.remove("treshold.lock")

@bot.event
async def on_member_update(before,after):
    if(config["member_role"]==0 or config["notification_channel"]==0):
        await before.guild.channels[0].send("You need configure your bot using !mine config")
        return False
    guild=before.guild
    members=guild.get_role(config["member_role"]).members
    channel=guild.get_channel(config["notification_channel"])

    server_on=is_server_running()
    if(count_players(members)<config["minimum_connected"] and is_server_running()):
        if not is_in_lock():
            set_lock()
            time_to_stop=time()+config["treshold"]
            print("Starting stopping")
            
            while(time()<time_to_stop and count_players(members)<config["minimum_connected"]):
                send_mc_message("Arrêt du serveur dans {} secondes".format(int(time_to_stop-time())))
                await sleep(15)

            if count_players(members)<config["minimum_connected"]:
                send_mc_message("Arrêt du serveur")
                await sleep(5)
                stop_server()
                await channel.send("Serveur arrêté")
            else:
                send_mc_message("Arrêt annulé")
                remove_lock()
        else:
            return None
    elif(count_players(members)>=config["minimum_connected"] and not is_server_running()):
        launch_server()
        await channel.send("Lancement du serveur par "+" ".join(["<@{}>".format(str(player.id)) for player in list_players(members)]))
        remove_lock()

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
            await message.channel.send("Treshold set to `{}s`".format(config["treshold"]))
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
        elif args[0]=="state":
            if is_server_running():
                await message.channel.send("✅ The server is online")
            else:
                await message.channel.send("❌ The server is offline")
        else:
            embed=discord.Embed(title="Minecraft launcher bot config",colour=discord.Colour(0x0000))
            embed.description="""**!mine setchannel** to set the notification channel, currently set to: <#{channel}>
            **!mine treshold** to set the treshold in seconds, currently set to: `{treshold}s`
            **!mine members_count** to set minimum members connected, currently set to: `{members}`
            **!mine role** to set the minecraft players role (you need to mention it), currently set to: `{role}`
            **!mine server** to set server launch command, currently set to: `{command}`
            **!mine state** print the state of the server""".format(
                treshold=config["treshold"],
                members=config["minimum_connected"],
                command=config["server_executable"],
                channel=config["notification_channel"],
                role=role)
            embed.set_footer(text="Bot made by RedBlaze#0645")
            await message.channel.send(embed=embed)

remove_lock()
bot.run(config["token"])