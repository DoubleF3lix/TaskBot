import os

import discord
from cogs.create_project import CreateProjectCog
from cogs.create_task import CreateTaskCog
from cogs.edit_project import EditProjectCog
from cogs.exec_query import ExecQueryCog
from cogs.purge_employees import PurgeEmployeesCog
from cogs.register_employee import RegisterEmployeeCog
from cogs.sync import SyncCog
from cogs.update_employee import UpdateEmployeeCog
from cogs.update_usernames import UpdateUsernamesCog
from database_connection import DatabaseConnection
from discord import Intents
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()


class PrimaryBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="/", intents=Intents.default())

        self.db = DatabaseConnection(self, os.environ["DB_LOGIN"])
        self.query = self.db.session.query
        self.add_obj = self.db.session.add
        self.commit = self.db.session.commit

    async def get_or_fetch_channel(self, id: int) -> discord.abc.GuildChannel | discord.Thread | None:
        """
        get_or_fetch_channel - Gets a channel, first trying the cache, and then making an API call if couldn't be found

        Args:
            id (int): The ID of the channel to fetch

        Returns:
            discord.abc.GuildChannel | discord.Thread | None: The channel object, or None if it could not be found
        """
        try:
            if channel_get_attempt := self.get_channel(id):
                return channel_get_attempt
            else:
                return await self.fetch_channel(id)
        except discord.NotFound:
            return None

    async def setup_hook(self):
        # DB Admins
        await self.add_cog(ExecQueryCog(self, 5))
        await self.add_cog(UpdateUsernamesCog(self, 5))
        await self.add_cog(PurgeEmployeesCog(self, 5))
        await self.add_cog(SyncCog(self))  # Already restricted to is_owner() of bot

        # Directors
        await self.add_cog(RegisterEmployeeCog(self, 4))

        # Managers
        await self.add_cog(CreateProjectCog(self, 3))
        await self.add_cog(UpdateEmployeeCog(self, 3))
        await self.add_cog(EditProjectCog(self, 3))

        # Tier 2 Employee
        await self.add_cog(CreateTaskCog(self, 2))

        # Tier 1 Employee


PrimaryBot().run(os.environ["DISCORD_TOKEN"])
