import typer

from mysk.commands.dev.list import dev_list
from mysk.commands.dev.mark import dev_mark
from mysk.commands.dev.migrate import dev_migrate

app = typer.Typer(
    help="Developer utilities for skill lifecycle management.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

app.command("list")(dev_list)
app.command("mark")(dev_mark)
app.command("migrate")(dev_migrate)
