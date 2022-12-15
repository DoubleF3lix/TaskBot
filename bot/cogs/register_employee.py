from typing import TYPE_CHECKING

import discord
from const import WHITE_X_MARK
from database_obj import *
from discord import Interaction, app_commands
from discord.ext import commands
from sqlalchemy.exc import IntegrityError

if TYPE_CHECKING:
    from main import PrimaryBot


class RegisterEmployeeCog(commands.Cog):
    def __init__(self, bot: commands.Bot, access_level: int):
        self.bot: PrimaryBot = bot
        self.access_level = access_level

    @app_commands.command(name="register_employee")
    async def register_employee(
        self,
        interaction: Interaction,
        user: discord.Member,
        access_level: app_commands.Range[int, 1, 4] = 1,
    ):
        if not self.bot.db.check_access_level(interaction.user.id, self.access_level):
            await interaction.response.send_message(
                ":lock: Insufficient permissions. Please contact an administrator if you believe this is an issue.",
                ephemeral=True,
            )
            return

        # Users of access level 4 can only set 1-3, users of access level 5 can only set 1-4
        sender_access_level = self.bot.db.get_access_level(
            interaction.user.id
        )
        if sender_access_level <= access_level:
            await interaction.response.send_message(
                f"{WHITE_X_MARK} You cannot register an employee to an equal or higher access level than your own.",
                ephemeral=True,
            )
            return

        new_employee = Employee(
            username=user.nick or user.name,
            discord_id=user.id,
            access_level=access_level,
        )
        self.bot.add_obj(new_employee)

        try:
            self.bot.commit()
        except IntegrityError:
            await interaction.response.send_message(
                f"{WHITE_X_MARK} Employee is already registered.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f":white_check_mark: Successfully registered {user.mention} as an employee with access level {access_level}.",
            ephemeral=True,
        )
