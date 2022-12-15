from typing import TYPE_CHECKING

from discord.ext import commands
from discord.ext.commands import Context

if TYPE_CHECKING:
    from main import PrimaryBot


class SyncCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: PrimaryBot = bot

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def sync(self, ctx: Context):
        await ctx.send("Syncing...")
        await self.bot.tree.sync()
        await ctx.send("Synced!")
