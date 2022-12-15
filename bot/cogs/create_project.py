from typing import TYPE_CHECKING

import discord
from const import *
from database_obj import *
from discord import Interaction, app_commands, ui
from discord.ext import commands

if TYPE_CHECKING:
    from main import PrimaryBot


class CreateProjectUI(ui.Modal):
    # Initialize the UI with fields
    name = ui.TextInput(label="Project Name", required=True)
    description = ui.TextInput(
        label="Project Description",
        style=discord.TextStyle.paragraph,
        required=False,
        placeholder="Optional",
    )
    docs_link = ui.TextInput(
        label="Documentation Link",
        required=False,
        placeholder="https://docs.google.com/...",
    )
    repo_link = ui.TextInput(
        label="Repository Link",
        required=False,
        placeholder="https://github.com/Tinkrew/...",
    )
    storage_link = ui.TextInput(
        label="Storage Link", required=False, placeholder="https://drive.google.com/..."
    )

    def __init__(self, bot: commands.Bot):
        super().__init__(title="Create Project")
        self.bot: PrimaryBot = bot

    async def on_submit(self, interaction: Interaction):
        # Create the forum channel
        project_forum_channel: discord.ForumChannel = await self.bot.get_guild(
            GUILD_ID
        ).create_forum(
            name=self.name.value.replace(" ", "-").lower(),
            category=self.bot.get_channel(PROJECTS_CATEGORY_ID),
            overwrites={
                self.bot.get_guild(GUILD_ID).default_role: discord.PermissionOverwrite(send_messages=False)
            }
        )

        # I don't care that it's not a word
        stati: list[Status] = self.bot.query(Status).all()
        for status in stati:
            await project_forum_channel.create_tag(name=status.name, emoji=status.emoji, moderated=True)

        # Create the embed the "General Discussion Thread" will be initialized with
        main_thread_embed = discord.Embed(
            color=discord.Color(4705791),
            title=self.name.value,
            description=self.description.value,
        )
        # Don't add embed parameters if they weren't defined (since they're not required)
        if self.docs_link.value:
            main_thread_embed.add_field(
                name="Documentation", value=self.docs_link.value, inline=False
            )
        if self.repo_link.value:
            main_thread_embed.add_field(
                name="Repository", value=self.repo_link.value, inline=False
            )
        if self.storage_link.value:
            main_thread_embed.add_field(
                name="Storage", value=self.storage_link.value, inline=False
            )
        main_thread_embed.add_field(name="Total Tasks", value="0", inline=True)
        main_thread_embed.add_field(name="Completed Tasks", value="0", inline=True)
        main_thread_embed.add_field(name="Incomplete Tasks", value="0", inline=True)

        # Create the "General Discussion Thread" and initialize it with the embed
        main_thread: discord.channel.ThreadWithMessage = (
            await project_forum_channel.create_thread(
                name="General Discussion", embed=main_thread_embed
            )
        )
        # Pin the embed in the thread, and pin the thread itself in the forum
        await main_thread.thread.edit(pinned=True)
        await main_thread.message.pin()

        new_project = Project(
            name=self.name.value,
            description=self.description.value or None,
            docs_link=self.docs_link.value or None,
            repo_link=self.repo_link.value or None,
            storage_link=self.storage_link.value or None,
            discord_forum_channel_id=project_forum_channel.id,
            discord_main_thread_id = main_thread.thread.id,
            discord_main_thread_first_message_id=main_thread.message.id,
        )
        self.bot.add_obj(new_project)
        self.bot.commit()

        await interaction.response.send_message(
            f":white_check_mark: Successfully created project in {project_forum_channel.mention}", ephemeral=True
        )


class CreateProjectCog(commands.Cog):
    def __init__(self, bot: commands.Bot, access_level: int):
        self.bot: PrimaryBot = bot
        self.access_level = access_level

    @app_commands.command(name="create_project")
    async def create_project(self, interaction: Interaction):
        if not self.bot.db.check_access_level(interaction.user.id, self.access_level):
            await interaction.response.send_message(
                ":lock: Insufficient permissions. Please contact an administrator if you believe this is an issue.",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(CreateProjectUI(self.bot))
