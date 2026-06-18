import typer

from mysk.commands import deploy, init
from mysk.commands import list as list_cmd
from mysk.commands.dev import app as dev_app

app = typer.Typer(
    name="mysk",
    help="Manage and deploy agent skills.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

app.add_typer(dev_app, name="dev")

app.command("list")(list_cmd.list_skills)
app.command("deploy")(deploy.deploy)
app.command("init")(init.init)
