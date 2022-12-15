from typing import TYPE_CHECKING

import discord
from const import GUILD_ID
from database_obj import *
from discord import Interaction, app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from main import PrimaryBot


class PurgeEmployeesCog(commands.Cog):
    def __init__(self, bot: commands.Bot, access_level: int):
        self.bot: PrimaryBot = bot
        self.access_level = access_level

    @app_commands.command(name="purge_employees")
    async def purge_employees(self, interaction: Interaction):
        if not self.bot.db.check_access_level(interaction.user.id, self.access_level):
            await interaction.response.send_message(
                ":lock: Insufficient permissions. Please contact an administrator if you believe this is an issue.",
                ephemeral=True,
            )
            return

        current_employees: list[Employee] = self.bot.db.get_filtered_employees()
        purged_users = []
        for employee in current_employees:
            try:
                await self.bot.db.get_employee_member(employee_id=employee.id)
            except discord.NotFound:
                purged_users.append(f'{employee.username} ({str(employee.discord_id)})')
                employee.username = None
                employee.access_level = 0

        self.bot.commit()

        await interaction.response.send_message(f":white_check_mark: The following employees were successfully purged:{chr(10)}{chr(10).join(purged_users)}" if purged_users else ":white_check_mark: No usernames were updated.", ephemeral=True)
