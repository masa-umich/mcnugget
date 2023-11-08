from mcnugget.cli.instrument import instrument
import click


@click.group()
def mcnugget():
    ...


mcnugget.add_command(instrument)
