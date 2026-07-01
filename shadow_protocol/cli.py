"""CLI entrypoint for Shadow Protocol Studio."""

import click


@click.command()
@click.argument("case_id", required=True)
@click.option("--dry-run", is_flag=True, help="Simulate pipeline without LLM calls")
@click.option("--from", "resume_step", help="Resume from a specific pipeline stage")
@click.option("--batch", help="Comma-separated list of case IDs to process")
def main(case_id: str, dry_run: bool, resume_step: str | None, batch: str | None):
    """Create a Shadow Protocol video episode."""

    click.echo(f"Shadow Protocol Studio v0.1.0")
    click.echo(f"Case: {case_id}")
    if dry_run:
        click.echo("Mode: dry-run (simulation)")
    if resume_step:
        click.echo(f"Resume from: {resume_step}")
    if batch:
        click.echo(f"Batch mode: {batch}")

    from shadow_protocol.lib.orchestrator_runner import run_pipeline

    exit_code = run_pipeline(
        case_id=case_id,
        dry_run=dry_run,
        resume_step=resume_step,
    )
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
