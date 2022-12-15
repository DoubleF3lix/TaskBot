import sqlalchemy
from sqlalchemy import CheckConstraint, Column, ForeignKey
from sqlalchemy.dialects.mysql import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import session
from sqlalchemy.sql import func
from sqlalchemy.sql.elements import TextClause

Base = declarative_base()


class Employee(Base):
    __tablename__ = "Employee"
    __table_args__ = (CheckConstraint("access_level BETWEEN 0 AND 5"),)

    id = Column(INTEGER(unsigned=True), primary_key=True)
    username = Column(VARCHAR(100)) # We technically don't need to store the username, but it can make usage of exec_query a little easier
    discord_id = Column(BIGINT(unsigned=True), unique=True)
    access_level = Column(
        TINYINT(unsigned=True), nullable=False, server_default=TextClause("1")
    )
    utc_offset = Column(TINYINT())
    date_joined = Column(DATETIME(), server_default=func.utc_timestamp())


class Project(Base):
    __tablename__ = "Project"

    id = Column(SMALLINT(unsigned=True), primary_key=True)
    name = Column(VARCHAR(150), nullable=False, unique=True)
    description = Column(VARCHAR(2000))
    docs_link = Column(VARCHAR(2000))
    repo_link = Column(VARCHAR(2000))
    storage_link = Column(VARCHAR(2000))
    date_created = Column(
        DATETIME(), nullable=False, server_default=func.utc_timestamp()
    )
    # We need to store this (and not just fetch it from discord_main_thread_id.parent since we need to check the parent from any thread (like slash commands run from task threads))
    discord_forum_channel_id = Column(BIGINT(unsigned=True))
    # We don't need to store the main message of the main thread since the first message of a thread and that thread have the same ID
    discord_main_thread_id = Column(BIGINT(unsigned=True))


class Department(Base):
    __tablename__ = "Department"

    id = Column(TINYINT(unsigned=True), primary_key=True)
    name = Column(VARCHAR(50), nullable=False, unique=True)


class EmployeeDepartment(Base):
    __tablename__ = "EmployeeDepartment"

    employee_id = Column(
        INTEGER(unsigned=True), ForeignKey("Employee.id"), primary_key=True
    )
    department_id = Column(
        TINYINT(unsigned=True), ForeignKey("Department.id"), primary_key=True
    )


class Status(Base):
    __tablename__ = "Status"

    id = Column(TINYINT(unsigned=True), primary_key=True)
    name = Column(VARCHAR(50), nullable=False, unique=True)
    emoji = Column(VARCHAR(50))


class Task(Base):
    __tablename__ = "Task"

    id = Column(INTEGER(unsigned=True), primary_key=True)
    project_id = Column(
        SMALLINT(unsigned=True), ForeignKey("Project.id"), nullable=False
    )
    name = Column(VARCHAR(150), nullable=False)
    description = Column(VARCHAR(2000))
    parent_task_id = Column(BIGINT(unsigned=True))
    due_date = Column(DATE())
    department = Column(TINYINT(unsigned=True), ForeignKey("Department.id"))
    status = Column(TINYINT(unsigned=True), ForeignKey("Status.id"))
    date_created = Column(
        DATETIME(), nullable=False, server_default=func.utc_timestamp()
    )
    discord_thread_channel_id = Column(BIGINT(unsigned=True))
    # We don't need to store the main message of the main thread since the first message of a thread and that thread have the same ID


class TaskAssignee(Base):
    __tablename__ = "TaskAssignee"

    task_id = Column(INTEGER(unsigned=True), ForeignKey("Task.id"), primary_key=True)
    employee_id = Column(
        INTEGER(unsigned=True), ForeignKey("Employee.id"), primary_key=True
    )


class TaskDependency(Base):
    __tablename__ = "TaskDependency"
    __table_args__ = (CheckConstraint("parent_task_id != child_task_id"),)

    parent_task_id = Column(
        INTEGER(unsigned=True), ForeignKey("Task.id"), primary_key=True
    )
    child_task_id = Column(
        INTEGER(unsigned=True), ForeignKey("Task.id"), primary_key=True
    )


class Asset(Base):
    __tablename__ = "Asset"

    id = Column(INTEGER(unsigned=True), primary_key=True)
    task_id = Column(INTEGER(unsigned=True), ForeignKey("Task.id"), nullable=False)
    asset_link = Column(VARCHAR(2000), nullable=False)
    date_created = Column(
        DATETIME(), nullable=False, server_default=func.utc_timestamp()
    )


def create_db(engine: sqlalchemy.engine.Engine, session: session.Session):
    # This won't create tables that already exist
    Base.metadata.create_all(engine)

    # But this will run, so we have to check to make sure the table is empty before populating it
    if not session.query(Department).first():
        session.execute(
            insert(Department),
            [
                {"name": "Mechanic"},
                {"name": "Developer"},
                {"name": "Artist"},
                {"name": "Builder"},
                {"name": "Marketing"},
                {"name": "Finance"},
                {"name": "HR"},
            ],
        )

    if not session.query(Status).first():
        session.execute(
            insert(Status),
            [
                {"name": "Unassigned", "emoji": "\U0000269C"},
                {"name": "Assigned", "emoji": "\U0001F530"},
                {"name": "In Progress", "emoji": "\U0001F536"},
                {"name": "Stuck", "emoji": "\U0001F6D1"},
                {"name": "Feedback", "emoji": "\U0001F4AC"},
                {"name": "Complete", "emoji": "\U00002705"},
            ],
        )

    session.commit()
