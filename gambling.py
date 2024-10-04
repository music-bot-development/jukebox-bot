import discord
from discord.ext import commands
import random

class GamblingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_points = {}  # Dictionary to store user points

    @commands.command(name="gamble", description="Gamble some of your points!")
    async def gamble(self, ctx, amount: int):
        user_id = ctx.author.id

        if user_id not in self.user_points:
            self.user_points[user_id] = 100  # Start users with 100 points

        if self.user_points[user_id] < amount:
            await ctx.send(f"You don't have enough points to gamble. You currently have {self.user_points[user_id]} points.")
            return

        if random.random() > 0.5:
            self.user_points[user_id] += amount
            await ctx.send(f"Congratulations! You won {amount} points. You now have {self.user_points[user_id]} points.")
        else:
            self.user_points[user_id] -= amount
            await ctx.send(f"Sorry, you lost {amount} points. You now have {self.user_points[user_id]} points.")

    @commands.command(name="points", description="Check how many points a user has.")
    async def points(self, ctx, user: discord.User):
        user_id = user.id
        if user_id not in self.user_points:
            self.user_points[user_id] = 100  # Start users with 100 points

        await ctx.send(f"<@{user_id}> has {self.user_points[user_id]} points.")

    @commands.command(name="leaderboard", description="Check the top users by points.")
    async def leaderboard(self, ctx):
        if not self.user_points:
            await ctx.send("No points have been recorded yet.")
            return

        sorted_users = sorted(self.user_points.items(), key=lambda x: x[1], reverse=True)
        leaderboard_text = "\n".join([f"<@{user_id}>: {points} points" for user_id, points in sorted_users[:10]])

        await ctx.send(f"**Leaderboard:**\n{leaderboard_text}")

    @commands.command(name="who-built-the-pyramids", description="Tells you the answer to who built the pyramids")
    async def who_built_the_pyramids(self, ctx):
        await ctx.send(file=discord.File('images/pyramids-aliens-meme.jpg'))

# Setup function to add the cog to the bot
def setup(bot):
    bot.add_cog(GamblingCog(bot))
