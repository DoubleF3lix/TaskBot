from typing import TYPE_CHECKING

import discord
from const import *
from database_obj import *
from discord import Interaction, app_commands, ui
from discord.ext import commands

if TYPE_CHECKING:
    from main import PrimaryBot


class EditProjectUI(ui.Modal):
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

    def __init__(self, bot: commands.Bot, project_id: int, project_main_thread_id: int):
        super().__init__(title="Edit Project")
        self.bot: PrimaryBot = bot
        self.project_id = project_id
        self.project_main_thread_id = project_main_thread_id

        self.name.default = self.bot.query(Project).filter_by(id=project_id).first().name

    async def on_submit(self, interaction: Interaction):
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

        # TODO update total task, completed tasks, and incomplete tasks fields in both task creation and task completion and deletion

        # Update the "General Discussion Thread" with the new embed\
        main_thread_channel: discord.Thread = self.bot.get_channel(self.project_main_thread_id)
        await main_thread_channel.parent.edit(
            name=self.name.value
        )

        await main_thread_channel.get_partial_message(self.project_main_thread_id).edit(embed=main_thread_embed)

        # Update the project in the database
        self.bot.query(Project).filter_by(id=self.project_id).update(
            {
                "name": self.name.value,
                "description": self.description.value,
                "docs_link": self.docs_link.value,
                "repo_link": self.repo_link.value,
                "storage_link": self.storage_link.value,
            }
        )
        self.bot.commit()

        await interaction.response.send_message(
            ":white_check_mark: Successfully modified project", ephemeral=True
        )


class EditProjectCog(commands.Cog):
    def __init__(self, bot: commands.Bot, access_level: int):
        self.bot: PrimaryBot = bot
        self.access_level = access_level

    @app_commands.command(name="edit_project")
    async def edit_project(self, interaction: Interaction):
        if not self.bot.db.check_access_level(interaction.user.id, self.access_level):
            await interaction.response.send_message(
                ":lock: Insufficient permissions. Please contact an administrator if you believe this is an issue.",
                ephemeral=True,
            )
            return

        if not isinstance(interaction.channel, discord.Thread) or not isinstance(
            interaction.channel.parent, discord.ForumChannel
        ):
            await interaction.response.send_message(
                f"{WHITE_X_MARK} This command must be used in a project forum channel.",
                ephemeral=True,
            )
            return

        project_forum_channel: discord.ForumChannel = interaction.channel.parent
        # Check if the parent forum channel is a valid project
        project_obj: Project
        if not (
            project_obj := self.bot.query(Project)
            .filter_by(discord_forum_channel_id=project_forum_channel.id)
            .first()
        ):
            await interaction.response.send_message(
                f"{WHITE_X_MARK} {project_forum_channel.mention} is not a valid project.",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(EditProjectUI(self.bot, project_obj.id, project_obj.discord_main_thread_id))
