import logging
from pathlib import Path

import click
from jinja2 import Environment, FileSystemLoader
from tqdm import tqdm

from ._dwarf import DWARFContext
from .filters import do_grouped_member_sections, do_insert_name, do_ns_actions, do_ns_chain
from .post_process import cleanup
from .visitor import Visitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dwarf2cpp")


@click.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--base-dir", type=str, required=True, help="Base directory used during compilation.")
@click.option(
    "--output-path",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory for generated files. Defaults to 'out' inside the input file's directory.",
)
@click.option(
    "--grouped-output-path",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory for grouped generated files. Defaults to 'grouped' inside the output directory.",
)
def main(path: Path, base_dir: str, output_path: Path | None, grouped_output_path: Path | None):
    output_path = output_path or (path.parent / "out")
    grouped_output_path = grouped_output_path or (output_path / "grouped")

    if output_path.resolve() == grouped_output_path.resolve():
        raise click.BadParameter(
            "Grouped output path must be different from output path.",
            param_hint="--grouped-output-path",
        )

    logger.info(f'Creating DWARF context for "{path.absolute()}"')
    ctx = DWARFContext(str(path))
    visitor = Visitor(ctx, base_dir)

    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(template_dir), keep_trailing_newline=True)
    env.filters["ns_chain"] = do_ns_chain
    env.filters["ns_actions"] = do_ns_actions
    env.filters["insert_name"] = do_insert_name
    env.filters["grouped_member_sections"] = do_grouped_member_sections

    for rel_path, file in (pbar := tqdm(visitor.files)):
        for root, grouped_members in ((output_path, False), (grouped_output_path, True)):
            result = env.get_template("file.jinja").render(file=file, grouped_members=grouped_members)
            result = cleanup(result)
            output_file = root / rel_path
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with output_file.open("w", encoding="utf-8") as f:
                f.write(result)

        pbar.set_description_str(f"Generating file: {rel_path}")

    logger.info(f"Done! Source-order files generated in: {output_path.absolute()}")
    logger.info(f"Done! Grouped files generated in: {grouped_output_path.absolute()}")
