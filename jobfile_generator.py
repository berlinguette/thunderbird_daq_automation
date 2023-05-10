import click
import re
from typing import List, Optional
from jobfile_generator.pbs_credentials import PbsCreds
from pathlib import Path

pbs_creds = PbsCreds()  # type: ignore VSCode, .env will populate params


@click.command()
def generate_jobfile():
    walltime = get_formatted_walltime()

    cpus = click.prompt("How many CPUs do you want", default=16, prompt_suffix="?")
    memory = click.prompt(
        "How much memory do you want (in GB)", default=64, prompt_suffix="?"
    )
    notify = click.confirm(
        "Do you want conversion status notifications by email",
        default=True,
        prompt_suffix="?",
    )
    if notify:
        email = click.prompt("What email address should we use", prompt_suffix="?")
    else:
        email = None

    click.echo(
        "Make sure all your data sources are in the 'project/input_data/unconverted' folder."
    )

    more = True
    sources: List[str] = []
    while more:
        source: str = click.prompt("Full name of data source")
        sources.append(source)
        more = click.confirm("Any more data sources", default=False, prompt_suffix="?")

    pbs_file_lines = _generate_file_lines(
        sources, walltime, cpus, memory, notify, email
    )
    # This needs to be run from repo root to work properly
    jobfile_path = Path(__file__).parent / "thunderbird_psd.pbs"
    with open(jobfile_path, "w") as jobfile:
        jobfile.writelines(pbs_file_lines)

    click.echo(f"Jobfile created at {jobfile_path}")
    ...  # STUB


def get_formatted_walltime() -> str:
    default_hours = 1
    default_minutes = 0
    walltime = f"{default_hours:02}:{default_minutes:02}:00"
    prompt_default_hours = f"{default_hours}h" if default_hours > 0 else ""
    prompt_default_minutes = f"{default_minutes}m" if default_minutes > 0 else ""
    prompt_default = prompt_default_hours + prompt_default_minutes
    
    valid = False
    while not valid:
        prompt_result = click.prompt(
            "How much processing time do you need (as '?h?m')",
            default=prompt_default,
            prompt_suffix="?",
        )
        prompt_result = prompt_result.lower().replace(" ", "")

        try:
            wall_hours = _parse_walltime(prompt_result, r"(\d+)h", "Hours")
        except (ValueError, IndexError):
            continue

        try:
            wall_minutes = _parse_walltime(prompt_result, r"(\d+)m", "Minutes")
        except (ValueError, IndexError):
            continue

        if wall_hours == 0 and wall_minutes == 0:
            click.echo("Please enter a non-zero time in the correct format ('?h?m').")
            continue

        walltime = f"{wall_hours:02}:{wall_minutes:02}:00"
        valid = True
    return walltime


def _parse_walltime(walltime: str, regex_string: str, time_section: str):
    time_section = time_section.capitalize()

    match = re.search(regex_string, walltime)
    if match:
        try:
            walltime_section = int(match.group(1))
        except (ValueError, IndexError):
            click.echo(f"That value was invalid. {time_section} must be an integer")
            raise
    else:
        walltime_section = 0
    return walltime_section


def _generate_file_lines(
    sources: List[str],
    walltime: str,
    cpus: int,
    memory: int,
    notify: bool,
    email: Optional[str] = None,
) -> List[str]:
    if notify and email is not None:
        notify_line = "#PBS -m abe"
        email_line = f"#PBS -M {email}"
    else:
        notify_line = None
        email_line = None
    alloc_code = pbs_creds.alloc_code

    source_lines = [
        f"-s \"/arc/project/{alloc_code}/input_data/unconverted/{source}\" \\"
        if i == 0
        else f"\"/arc/project/{alloc_code}/input_data/unconverted/{source}\" \\"
        for i, source in enumerate(sources)
    ]

    pbs_file_lines: List[Optional[str]] = [
        "#!/bin/bash",
        "",
        f"#PBS -l walltime={walltime},select=1:ncpus={cpus}:mem={memory}gb",
        "#PBS -N thunderbird_data_converter",
        f"#PBS -A {alloc_code}",
        notify_line,
        email_line,
        f"#PBS -W group_list={alloc_code}-rw",
        "#PBS -W umask=007",
        "",
        "#################################################",
        "",
        "module load python/3.8.10",
        "module load py-virtualenv/16.7.6",
        "",
        "cd $PBS_O_WORKDIR/thunderbird_daq_automation",
        "source .venv/bin/activate",
        "",
        "python src/data_converter.py \\",
        *source_lines,
        "-d \"/scratch/st-cberling-1/output_data/conversion/\" \\",
        "--fresh-destination --csv-tasks 4",
        "",
        "deactivate",
    ]
    return [f"{line}\n" for line in pbs_file_lines if line is not None]


if __name__ == "__main__":
    generate_jobfile()
