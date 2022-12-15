from typing import TYPE_CHECKING

import discord
from const import GUILD_ID, WHITE_X_MARK
from database_obj import *
from discord import Interaction, app_commands
from discord.ext import commands
from sqlalchemy.engine.cursor import CursorResult

if TYPE_CHECKING:
    from main import PrimaryBot


class UpdateUsernamesCog(commands.Cog):
    def __init__(self, bot: commands.Bot, access_level: int):
        self.bot: PrimaryBot = bot
        self.access_level = access_level

    @app_commands.command(name="update_usernames")
    async def update_usernames(self, interaction: Interaction):
        if not self.bot.db.check_access_level(interaction.user.id, self.access_level):
            await interaction.response.send_message(
                ":lock: Insufficient permissions. Please contact an administrator if you believe this is an issue.",
                ephemeral=True,
            )
            return

        # Loop through all the employees
        current_employees: list[Employee] = self.bot.db.get_filtered_employees()
        updated_users = []
        missing_users = []
        for employee in current_employees:
            try:
                # Get the member object
                member: discord.Member = await self.bot.db.get_employee_member(employee_id=employee.id)
                # If their nickname is outdated, update it
                if (member.nick or member.name) != employee.username:
                    updated_users.append(f'`{employee.username}` => `{member.nick or member.name}` (ID: {str(member.id)})')
                    employee.username = member.nick or member.name
            # If we couldn't find them, add them to the missing users list
            except discord.NotFound:
                missing_users.append(f'{employee.username} ({str(employee.discord_id)})')

        self.bot.commit()

        missing_users_fail_string = f"\n\nFailed to find the following users:{chr(10)}{chr(10).join(missing_users)}{chr(10) * 2}This may be because of a discord API error, or they have left the server and require manual purging via `/purge_employees`." if missing_users else ""
        success_message = f":white_check_mark: The following usernames were successfully updated:{chr(10)}{chr(10).join(updated_users)}" if updated_users else ":white_check_mark: No usernames were updated."

        await interaction.response.send_message(f"{success_message} {missing_users_fail_string}", ephemeral=True)
