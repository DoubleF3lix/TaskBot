from datetime import datetime
from typing import TYPE_CHECKING, Literal

import discord
from const import GUILD_ID, WHITE_X_MARK
from database_obj import *
from discord import Interaction, app_commands, ui
from discord.app_commands import Choice
from discord.ext import commands

if TYPE_CHECKING:
    from main import PrimaryBot


async def create_task_handler(
    bot: commands.Bot,
    interaction: discord.Interaction,
    project_forum_channel: discord.ForumChannel,
    project_id: int,
    task_name: str,
    description: str = None,
    department: Choice = None,
    parent_task_thread: discord.Thread = None,
):
    bot: PrimaryBot = bot  # PrimaryBot is not defined when trying to type hint this in the function header, so we have to redefine it here to get the proper type hint

    # Create the embed the "General Discussion Thread" will be initialize with
    task_thread_embed = discord.Embed(
        color=discord.Color(4705791),
        title=task_name,
        description=description,
    )
    task_thread_embed.add_field(
        name="Parent Task",
        value=(parent_task_thread.mention if parent_task_thread else None)
        or "None Set",
        inline=True,
    )
    task_thread_embed.add_field(name="Assignee", value="None Set", inline=True)
    task_thread_embed.add_field(name="Due Date", value="None Set", inline=True)
    task_thread_embed.add_field(
        name="Department",
        value=(department.name if department else None) or "None Set",
        inline=True,
    )
    task_thread_embed.add_field(name="Status", value="Unassigned", inline=True)

    task_thread: discord.channel.ThreadWithMessage = (
        await project_forum_channel.create_thread(
            name=task_name, embed=task_thread_embed
        )
    )
    await task_thread.message.pin()

    # Update the database with the new project
    new_project = Task(
        project_id=project_id,
        name=task_name,
        description=description,
        department=department.value if department else None,
        parent_task_id=parent_task_thread.id if parent_task_thread else None,
        discord_thread_channel_id=task_thread.thread.id,
    )
    bot.add_obj(new_project)
    bot.commit()

    await interaction.response.send_message(
        f":white_check_mark: Successfully created task in {task_thread.thread.mention}",
        ephemeral=True,
    )


class CreateTaskCog(commands.Cog):
    def __init__(self, bot: commands.Bot, access_level: int):
        self.bot: PrimaryBot = bot
        self.access_level = access_level

    @app_commands.command(name="create_task")
    @app_commands.choices(
        department=[
            Choice(name="Mechanic", value=1),
            Choice(name="Developer", value=2),
            Choice(name="Artist", value=3),
            Choice(name="Builder", value=4),
            Choice(name="Marketing", value=5),
            Choice(name="Finance", value=6),
            Choice(name="HR", value=7),
        ]
    )
    async def create_task(
        self,
        interaction: Interaction,
        task_name: str,
        description: str = None,
        department: Choice[int] = None,
        parent_task: discord.Thread = None,
    ):
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
        else:
            project_id: int = project_obj.id

        # TODO modal stuff, subgroup

        # Make sure the parent task is valid (not set to itself and is a valid task channel)
        if parent_task and (
            not self.bot.query(Task)
            .filter_by(discord_thread_channel_id=parent_task.id)
            .first()
        ):
            await interaction.response.send_message(
                f"{WHITE_X_MARK} {parent_task.mention} is not a valid task.",
                ephemeral=True,
            )
            return

        await create_task_handler(
            self.bot,
            interaction,
            project_forum_channel,
            project_id,
            task_name,
            description,
            due_date=None,
            department=department,
            parent_task_thread=parent_task,
        )
