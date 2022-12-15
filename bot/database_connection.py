from typing import TYPE_CHECKING

import discord
import sqlalchemy
import sqlalchemy.orm
from const import GUILD_ID
from database_obj import *
from discord.ext import commands
from sqlalchemy.engine.cursor import CursorResult
from tabulate import tabulate

if TYPE_CHECKING:
    from main import PrimaryBot


class DatabaseConnection:
    def __init__(self, bot: commands.Bot, engine_string: str):
        """
        DatabaseConnection - Represents a connection to a MariaDB database with several abstractions

        Args:
            bot (commands.Bot): The discord bot instance
            engine_string (str): The connection string to the database
        """
        self.bot: PrimaryBot = bot
        self.engine = sqlalchemy.create_engine(engine_string)

        Session = sqlalchemy.orm.sessionmaker()
        Session.configure(bind=self.engine)
        self.session = Session()

        # create_db(self.engine, self.session)

    # Just a wrapper which automatically wraps the string into the sqlalchemy.text
    def execute(self, query: str, **kwargs) -> CursorResult:
        """
        execute - Wraps the query in sqlalchemy.text and executes it. This should only be used in special circumstances (or by ``/exec_query``), for more common SQL operations, see below:

        SQL operation alternatives:
        ``SELECT`` - ``session.query(TableOBJ)`` (aliased to ``bot.query``)
        ``INSERT`` - ``session.add(TableOBJ(param=arg))`` (aliased to ``bot.add_obj``). Needs committing via ``session.commit`` (aliased to ``bot.commit``).
        ``UPDATE`` - ``session.query(TableOBJ).filter_by(param=arg).update({param: arg})`` or ``ExistingTableOBJ.param = arg`` (useful if editing existing object from a ``SELECT`` statement). Needs committing via ``session.commit`` (aliased to ``bot.commit``).
        ``DELETE`` - ``session.query(TableOBJ).filter_by(param=arg).delete()``. Needs committing via ``session.commit`` (aliased to ``bot.commit``).

        Args:
            query (str): The SQL query to execute

        Returns:
            CursorResult: The result of the cursor. This can be passed to ``style_query`` for a nice output when using SELECT statements. For further pretty printing and error handling, see the ``/exec_query`` command.
        """
        return self.engine.execute(sqlalchemy.text(query), **kwargs)

    def style_query(self, query_results: CursorResult) -> str:
        """
        style_query - Takes the result of a query and returns a pretty printed string using the ``tabulate`` library.

        Args:
            query_results (CursorResult): The direct output from query. This should be obtained by using ``execute`` or ``session.query.compile`` (use the former though, latter isn't tested... at all).

        Returns:
            str: The formatted table as a string
        """
        return tabulate(query_results.mappings().all(), headers="keys", tablefmt="psql")

    def get_access_level(
        self, *, discord_id: int = None, employee_id: int = None
    ) -> int:
        """
        get_access_level - Fetches the access level of an employee. Either ``discord_id`` or ``employee_id`` should be set. If both are set, ``discord_id`` will be used.

        Args:
            discord_id (int, optional): The discord ID of the employee to access. Most likely the better choice, since you can fetch it off a ``discord.Interaction`` object. Defaults to None.
            employee_id (int, optional): The ID of the employee to access. Better used if you already have an employee object from some other data. Defaults to None.

        Raises:
            ValueError: Neither ``discord_id`` nor ``employee_id`` were set

        Returns:
            int: The employee's access level, or 0 if the employee doesn't exist
        """
        employee: Employee

        if discord_id:
            employee = (
                self.session.query(Employee).filter_by(discord_id=discord_id).first()
            )
        elif employee_id:
            employee = (
                self.session.query(Employee).filter_by(employee_id=employee_id).first()
            )
        else:
            raise ValueError("Must specify either discord_id or employee_id")

        return employee.access_level if employee else 0

    def get_project(
        self, *, forum_channel_id: int = None, project_id: int = None
    ) -> Project | None:
        """
        get_project - Fetches a project object from the database. Either ``channel_id`` or ``project_id`` should be set. If both are set, ``channel_id`` will be used.

        Args:
            forum_channel_id (int, optional): The channel ID of a ``discord.ForumChannel`` object associated with the project to fetch. Most likely the better choice, since you can fetch it off a ``discord.Interaction`` object. Defaults to None.
            project_id (int, optional): The ID of the project to fetch. Defaults to None.

        Raises:
            ValueError: Neither ``channel_id`` nor ``project_id`` were set

        Returns:
            Project | None: The project object, or None if the project doesn't exist
        """
        if forum_channel_id:
            return (
                self.session.query(Project)
                .filter_by(discord_forum_channel_id=forum_channel_id)
                .first()
            )
        elif project_id:
            return self.session.query(Project).filter_by(project_id=project_id).first()
        else:
            raise ValueError("Must specify either forum_channel_id or project_id")

    def get_project_forum_channel(
        self, *, channel_id: int = None, project_id: int = None
    ) -> discord.ForumChannel:
        """
        get_project_forum_channel - Gets a forum channel object from a sub-thread or a project ID. Either ``channel_id`` or ``project_id`` should be set. If both are set, ``channel_id`` will be used.

        Args:
            channel_id (int, optional): The channel ID of a sub-thread of the project ID (so any of the task threads or the "General Discussion" thread). Defaults to None.
            project_id (int, optional): The ID of the project to get the forum channel of. Defaults to None.

        Raises:
            ValueError: Neither ``channel_id`` nor ``project_id`` were set
            ValueError: The channel is not a forum channel
            ValueError: The channel is not a valid project forum channel

        Returns:
            discord.ForumChannel: The forum channel object of the project
        """
        if channel_id:
            channel: discord.abc.GuildChannel = self.bot.get_or_fetch_channel(channel_id)

            if not isinstance(channel, discord.ForumChannel):
                raise ValueError("Channel is not a forum channel")
            if (
                self.bot.query(Project)
                .filter_by(discord_forum_channel_id=channel.id)
                .first()
            ):
                return channel
            else:
                raise ValueError("Channel is not a valid project forum channel")

        elif project_id:
            project_obj: Project = (
                self.session.query(Project).filter_by(project_id=project_id).first()
            )
            return self.bot.get_or_fetch_channel(project_obj.discord_forum_channel_id)
        else:
            raise ValueError("Must specify either channel_id or project_id")

    def get_project_main_thread(
        self, *, channel_id: int = None, project_id: int = None
    ) -> discord.Thread:
        # TODO this should be fetched by getting the main thread (if channel_id, get parent, check DB for parent, then get main)
        project_obj: Project = None
        if channel_id:
            project_obj = (
                self.session.query(Project).filter_by(channel_id=channel_id).first()
            )
        elif project_id:
            project_obj = (
                self.session.query(Project).filter_by(project_id=project_id).first()
            )
        else:
            raise ValueError("Must specify either channel_id or project_id")
        return self.bot.get_guild(GUILD_ID).get_channel(
            project_obj.discord_main_thread_id
        )

    def get_project_main_message(
        self, *, channel_id: int = None, project_id: int = None
    ) -> discord.Message:
        if channel_id:
            return (
                self.session.query(Project)
                .filter_by(channel_id=channel_id)
                .first()
                .first_message
            )
        elif project_id:
            return (
                self.session.query(Project)
                .filter_by(project_id=project_id)
                .first()
                .first_message
            )
        else:
            raise ValueError("Must specify either channel_id or project_id")

    def get_employee(
        self,
        *,
        discord_id: int = None,
        employee_id: int = None,
        filter_access_level: bool = True,
    ) -> Employee | None:
        if discord_id:
            if filter_access_level:
                return (
                    self.session.query(Employee)
                    .filter_by(discord_id=discord_id)
                    .filter(Employee.access_level > 0)
                    .first()
                )
            return self.session.query(Employee).filter_by(discord_id=discord_id).first()
        elif employee_id:
            if filter_access_level:
                return (
                    self.session.query(Employee)
                    .filter_by(employee_id=employee_id)
                    .filter(Employee.access_level > 0)
                    .first()
                )
            return (
                self.session.query(Employee).filter_by(employee_id=employee_id).first()
            )
        else:
            raise ValueError("Must specify either discord_id or employee_id")

    def get_filtered_employees(self) -> list[Employee]:
        return self.session.query(Employee).filter(Employee.access_level > 0).all()

    def check_access_level(self, discord_id: int, access_level: int) -> bool:
        return self.get_access_level(discord_id) >= access_level

    def get_employee_member(
        self,
        *,
        discord_id: int = None,
        employee_id: int = None,
        filter_access_level: bool = True,
    ) -> discord.Member | None:
        if employee := self.get_employee(
            discord_id=discord_id,
            employee_id=employee_id,
            filter_access_level=filter_access_level,
        ):
            return self.bot.get_guild(GUILD_ID).get_member(employee.discord_id)
        return None

    def get_task(self, *, task_id: int = None, channel_id: int = None) -> Task | None:
        if task_id:
            return self.session.query(Task).filter_by(task_id=task_id).first()
        elif channel_id:
            return self.session.query(Task).filter_by(channel_id=channel_id).first()
        else:
            raise ValueError("Must specify either task_id or channel_id")
