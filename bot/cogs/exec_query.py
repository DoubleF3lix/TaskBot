import time
from io import StringIO
from typing import TYPE_CHECKING

import discord
from discord import Interaction, app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from main import PrimaryBot


class ExecQueryCog(commands.Cog):
    def __init__(self, bot: commands.Bot, access_level: int):
        self.bot: PrimaryBot = bot
        self.access_level = access_level

    @app_commands.command(name="exec_query")
    async def exec_query(
        self, interaction: Interaction, query: str, visible_to_all: bool = False
    ):
        if not self.bot.db.check_access_level(interaction.user.id, self.access_level):
            await interaction.response.send_message(
                ":lock: Insufficient permissions. Please contact an administrator if you believe this is an issue.",
                ephemeral=True,
            )
            return

        try:
            # Get query results and query execution time
            prev_time = time.time()
            query_result = self.bot.db.execute(query)
            query_time = round(time.time() - prev_time, 3)

            # Generate the initial status message
            output = f"Query OK, {query_result.rowcount} row(s) found/affected ({query_time}s)"
            # If there was any output from the query (like in a SELECT statement), add it to the output
            if query_result.returns_rows:
                output += f"\n\n{self.bot.db.style_query(query_result)}"

        except Exception as e:
            # This will likely not execute in the event of of invalid SQL, so calculate it here
            query_time = round(time.time() - prev_time, 3)
            output = f"Query failed ({query_time}s) with error:\n\n{str(e)}"

        # Send the output as a file so we can send more than 2000 characters
        file_obj = discord.File(StringIO(output), filename="query_result.txt")
        await interaction.response.send_message(
            file=file_obj, ephemeral=not visible_to_all
        )
