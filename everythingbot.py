import hikari
import lightbulb
import random
import requests
import asyncpraw
import time

# Info censored for privacy

bot = lightbulb.BotApp(prefix="*p", token="TOKEN",
                       intents=hikari.Intents.ALL_UNPRIVILEGED)


@bot.listen(hikari.ShardReadyEvent)
async def ready_listener(_):
	print("The bot is ready! Yay!")


# Reddit client setup
reddit = asyncpraw.Reddit(client_id="client_ID", client_secret="client_secret",
                          username="username", password="password", user_agent="user_agent")


# Embeds a reddit meme from your choice of subreddit and filter option
@bot.command()
@lightbulb.option("filter", "The filter you want to get memes from", str, required=False, choices=['hot', 'new', 'rising', 'top'], default="hot")
@lightbulb.option("subreddit", "The subreddit to get the post from", str, required=False, choices=['memes', 'dankmemes', 'wholesomememes'], default="dankmemes")
@lightbulb.command("meme", "Gets a random reddit meme")
@lightbulb.implements(lightbulb.SlashCommand)
async def meme(ctx: lightbulb.Context):
	subreddit = await reddit.subreddit(ctx.options.subreddit)
	post_list = []
	limit = 20
	if ctx.options.filter == "new":
		async for submission in subreddit.new(limit=limit):
			post_list.append(submission)
	elif ctx.options.filter == "rising":
		async for submission in subreddit.rising(limit=limit):
			post_list.append(submission)
	elif ctx.options.filter == "top":
		async for submission in subreddit.top(limit=limit):
			post_list.append(submission)
	else:
		async for submission in subreddit.hot(limit=limit):
			post_list.append(submission)

	output = random.choice(post_list)
	# Do not include nsfw
	while output.over_18:
		output = random.choice(post_list)
	name = output.title
	url = output.url

	embed = hikari.Embed(title=name)
	embed.set_image(url)
	embed.set_footer(f"Posted in r/{ctx.options.subreddit}")
	await ctx.respond(embed)


# Sends a weather forecast
@bot.command()
@lightbulb.option("location", "The location to get the weather report for", str, required=True)
@lightbulb.command("weather", "gets a weather forecast")
@lightbulb.implements(lightbulb.SlashCommand)
async def weather(ctx: lightbulb.Context):
	weather_api_key = "weather_api_key"

	endpoint = f"https://api.openweathermap.org/data/2.5/weather?q={ctx.options.location}&appid={weather_api_key}&units=metric"
	response = requests.get(endpoint)
	data = response.json()

	# Parse JSON
	description = data["weather"][0]["description"].title()
	temp = data["main"]["temp"]
	feels_like = data["main"]["feels_like"]
	humidity = data["main"]["humidity"]
	pressure = data["main"]["pressure"]
	wind_speed = data["wind"]["speed"]
	icon = data["weather"][0]["icon"]

	# Create embed
	embed = hikari.Embed(title="Current weather in " + ctx.options.location.title(), description=description)
	embed.set_thumbnail(f"https://openweathermap.org/img/w/{icon}.png")
	embed.add_field(name="Temperature", value=f"{temp}°C")
	embed.add_field(name="Feels like", value=f"{feels_like}°C")
	embed.add_field(name="Humidity", value=f"{humidity}%")
	embed.add_field(name="Pressure", value=f"{pressure} hPa")
	embed.add_field(name="Wind speed", value=f"{wind_speed} m/s")

	await ctx.respond(embed)


# Error handler
@bot.listen(lightbulb.CommandErrorEvent)
async def on_error(event: lightbulb.CommandErrorEvent):
	exception = event.exception.__cause__ or event.exception
	if isinstance(exception, lightbulb.CommandNotFound):
		await event.context.respond(
			f"{event.context.author.mention}, *****************.")
	elif isinstance(exception, lightbulb.NotEnoughArguments):
		await event.context.respond(f"{event.context.user.mention}, ***********************.")
	elif isinstance(exception, TypeError):
		await event.context.respond("***********************?")
	else:
		raise exception


# Insult bot functionality below
immune = ["***********"]
blocked = ["**********"]

insults_list = [
	"*****************",
]


def get_insults(guild_id=None, custom=False):
	if custom:
		custom_insults = []
		with open(f'{guild_id}_custom_insults.txt', 'r', encoding="ISO-8859-1") as db:
			for line in db.readlines():
				new_insult = line.strip()
				custom_insults.append(new_insult)
		insult = random.choice(custom_insults)

	else:
		insult = random.choice(insults_list)

	lowercase = insult[0].lower() + insult[1:]
	return lowercase


@bot.command()
@lightbulb.option("user", "User to greet", hikari.User)
@lightbulb.command("greet", "Greets the specified user")
@lightbulb.implements(lightbulb.SlashCommand)
async def greet(ctx: lightbulb.Context):
	await ctx.respond(f"Hi {ctx.options.user.mention}!")


@bot.command()
@lightbulb.option("custom", "Whether insult is custom", bool, choices=[True, False], default=False, required=False)
@lightbulb.option("repeats", "Number of insults", int, default=1, required=False, min_value=1, max_value=5)
@lightbulb.option("user", "User to insult", str, required=True)
@lightbulb.command("insult", "Insults the specified user")
@lightbulb.implements(lightbulb.SlashCommand)
async def insult(ctx: lightbulb.Context):
	if ctx.author.id in blocked:
		await ctx.respond(f"{ctx.author.mention}, ***********.")
	elif ctx.options.user in immune:
		await ctx.respond(
			f"Nice try {ctx.author.mention}, but unfortunately for you {ctx.options.user} is too cool to be insulted.")
	else:
		for i in range(ctx.options.repeats):
			time.sleep(0.2)
			await ctx.respond(f"{ctx.options.user}, {get_insults(ctx.guild_id, ctx.options.custom)}")


@bot.command()
@lightbulb.option("insult", "Your custom insult", str, required=True,
                  modifier=lightbulb.commands.OptionModifier.CONSUME_REST)
@lightbulb.command("add", "Adds a custom insult")
@lightbulb.implements(lightbulb.SlashCommand)
async def add(ctx: lightbulb.Context):
	with open(f'{ctx.guild_id}_custom_insults.txt', 'a', encoding="ISO-8859-1") as db:
		db.write(f"{ctx.options.insult}\n")
		await ctx.respond('New custom insult was added.')


@bot.command()
@lightbulb.command("list", "Lists custom insults")
@lightbulb.implements(lightbulb.SlashCommand)
async def list(ctx: lightbulb.Context):
	with open(f'{ctx.guild_id}_custom_insults.txt', 'r', encoding="ISO-8859-1") as db:
		insult_list = []
		for ind, line in enumerate(db.readlines()):
			insult = line.strip()
			insult_list.append(f"{ind + 1}. {insult}")
		await ctx.respond("Custom insults for this server:")
		await ctx.respond('\n'.join(insult_list))


def convert(range_str):
	result = []
	if not "," in range_str and not "-" in range_str:
		result.append(int(range_str))
	else:
		for part in range_str.split(','):
			if '-' in part:
				a, b = part.split('-')
				a, b = int(a), int(b)
				result.extend(range(a, b + 1))
			else:
				a = int(part)
				result.append(a)
	return [num - 1 for num in result]


@bot.command()
@lightbulb.option("indexes", "The indexes to be deleted", str, required=True,
                  modifier=lightbulb.commands.OptionModifier.CONSUME_REST)
@lightbulb.command("delete", "Deletes an insult")
@lightbulb.implements(lightbulb.SlashCommand)
async def delete(ctx: lightbulb.Context):
	db = open(f"{ctx.guild_id}_custom_insults.txt", "r", encoding = "ISO-8859-1")
	lines = db.readlines()
	db.close()

	with open(f"{ctx.guild_id}_custom_insults.txt", "w", encoding = "ISO-8859-1") as db:
		remove_indexes = convert(ctx.options.indexes)
		for ind, line in enumerate(lines):
			if not ind in remove_indexes:
				db.write(line)
	await ctx.respond("Custom insult successfully deleted.")
	with open(f'{ctx.guild_id}_custom_insults.txt', 'r', encoding = "ISO-8859-1") as db:
		insult_list = []
		for ind, line in enumerate(db.readlines()):
			insult = line.strip()
			insult_list.append(f"{ind + 1}. {insult}")
		await ctx.respond("Custom insults for this server:")
		await ctx.respond('\n'.join(insult_list))


bot.run()
