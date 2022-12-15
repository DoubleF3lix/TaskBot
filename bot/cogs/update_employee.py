from typing import TYPE_CHECKING

import discord
from const import WHITE_X_MARK
from database_obj import *
from discord import Interaction, app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from main import PrimaryBot


class UpdateEmployeeCog(commands.Cog):
    def __init__(self, bot: commands.Bot, access_level: int):
        self.bot: PrimaryBot = bot
        self.access_level = access_level

    @app_commands.command(name="update_employee")
    async def update_employee(
        self,
        interaction: Interaction,
        user: discord.Member,
        access_level: app_commands.Range[int, 1, 4] = None,
        utc_offset: int = None,
    ):
        if not self.bot.db.check_access_level(interaction.user.id, self.access_level):
            await interaction.response.send_message(
                ":lock: Insufficient permissions. Please contact an administrator if you believe this is an issue.",
                ephemeral=True,
            )
            return

        # Make sure user isn't trying to update themselves
        if interaction.user.id == user.id:
            await interaction.response.send_message(
                f"{WHITE_X_MARK} You cannot update yourself. Contact an admin to update your own access level, or use `/set_utc_offset` to set your UTC offset.",
                ephemeral=True,
            )
            return

        # Make sure one of the optional arguments were defined
        if not access_level and not utc_offset:
            await interaction.response.send_message(
                f"{WHITE_X_MARK} You must provide at least one of `access_level` or `utc_offset`.",
                ephemeral=True,
            )
            return

        # Make sure they're accessing a valid employee
        if not self.bot.db.get_employee(discord_id=user.id, filter_access_level=False):
            await interaction.response.send_message(
                f"{WHITE_X_MARK} {user.mention} is not a registered employee.",
                ephemeral=True,
            )
            return

        # Setting values
        if access_level:
            # Users of access level 3 can only set 1 or 2, users of access level 4 can only set 1, 2, or 3
            sender_access_level = self.bot.db.get_access_level(
                discord_id=interaction.user.id
            )
            user_access_level = self.bot.db.get_access_level(discord_id=user.id)
            if sender_access_level <= access_level:
                await interaction.response.send_message(
                    f"{WHITE_X_MARK} You cannot update a user to an equal or higher access level than your own.",
                    ephemeral=True,
                )
                return
            # Make sure a level 4 can't demote a level 4, or a level 3 demote a level 3
            elif sender_access_level == user_access_level:
                await interaction.response.send_message(
                    f"{WHITE_X_MARK} You cannot change the access level of someone with the same access level as you.",
                    ephemeral=True,
                )
                return

            self.bot.db.get_employee(
                discord_id=user.id, filter_access_level=False
            ).access_level = access_level

        if utc_offset:
            self.bot.db.get_employee(
                discord_id=user.id, filter_access_level=False
            ).utc_offset = utc_offset

        self.bot.commit()

        success_msg = (
            "[UH-OH: You should not be seeing this. Please contact an administrator.]"
        )
        if access_level and utc_offset:
            success_msg = "access level and UTC offset"
        elif access_level:
            success_msg = "access level"
        elif utc_offset:
            success_msg = "UTC offset"

        await interaction.response.send_message(
            f":white_check_mark: Successfully modified {user.mention}'s {success_msg}.",
            ephemeral=True,
        )
