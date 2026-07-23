import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
POWER_BI_ROOT = PROJECT_ROOT / "report" / "power_bi"
PBIP_PATH = POWER_BI_ROOT / "TorgstatAnalytics.pbip"
MODEL_ROOT = POWER_BI_ROOT / "TorgstatAnalytics.SemanticModel"
REPORT_ROOT = POWER_BI_ROOT / "TorgstatAnalytics.Report"
REPORT_DEFINITION_ROOT = REPORT_ROOT / "definition"
PAGES_ROOT = REPORT_DEFINITION_ROOT / "pages"
DEFINITION_ROOT = MODEL_ROOT / "definition"
TABLE_ROOT = DEFINITION_ROOT / "tables"

OBJECT_NAME_PATTERN = re.compile(r"^table\s+(.+)$")
COLUMN_NAME_PATTERN = re.compile(r"^\tcolumn\s+(.+)$")
MODEL_REF_PATTERN = re.compile(r"^ref table\s+(.+)$")
RELATIONSHIP_COLUMN_PATTERN = re.compile(
    r"^\t(?:fromColumn|toColumn):\s+([^\.]+)\.(.+)$"
)
MEASURE_DECLARATION_PATTERN = re.compile(r"^\tmeasure\s+(.+?)\s*=")


def unquote_tmdl_name(value: str) -> str:
    value = value.strip()
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    return value


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as file_handle:
        return json.load(file_handle)


def validate_measure_formats(
    table_name: str, lines: list[str], errors: list[str]
) -> None:
    """Require one format string inside each measure block.

    Column and measure properties use the same TMDL indentation. Counting every
    ``formatString`` in a table therefore produces false failures as soon as
    Power BI serializes formatted columns. Inspecting each measure block keeps
    the check scoped to the object it is intended to validate.
    """

    measure_starts = [
        index
        for index, line in enumerate(lines)
        if MEASURE_DECLARATION_PATTERN.match(line)
    ]

    for start in measure_starts:
        declaration = MEASURE_DECLARATION_PATTERN.match(lines[start])
        if declaration is None:
            continue

        end = len(lines)
        for index in range(start + 1, len(lines)):
            line = lines[index]
            if line.strip() and line.startswith("\t") and not line.startswith("\t\t"):
                end = index
                break

        format_count = sum(
            line.startswith("\t\tformatString:") for line in lines[start + 1 : end]
        )
        if format_count != 1:
            measure_name = declaration.group(1).strip()
            errors.append(
                f"{table_name}: measure {measure_name} must have exactly one "
                f"formatString, found {format_count}"
            )


def validate_json_entry_points(errors: list[str]) -> None:
    pbip = load_json(PBIP_PATH)
    report_path = pbip["artifacts"][0]["report"]["path"]
    if (POWER_BI_ROOT / report_path).resolve() != REPORT_ROOT.resolve():
        errors.append("PBIP report path does not resolve to TorgstatAnalytics.Report")

    report_definition = load_json(REPORT_ROOT / "definition.pbir")
    model_path = report_definition["datasetReference"]["byPath"]["path"]
    if (REPORT_ROOT / model_path).resolve() != MODEL_ROOT.resolve():
        errors.append("PBIR semantic model path does not resolve correctly")

    load_json(MODEL_ROOT / "definition.pbism")


def validate_report_definition(errors: list[str]) -> None:
    version = load_json(REPORT_DEFINITION_ROOT / "version.json")
    if not re.fullmatch(r"[1-9][0-9]*\.(0|[1-9][0-9]*)\.0", version["version"]):
        errors.append("version.json: invalid PBIR version")

    report = load_json(REPORT_DEFINITION_ROOT / "report.json")
    if "themeCollection" not in report:
        errors.append("report.json: missing themeCollection")

    pages = load_json(PAGES_ROOT / "pages.json")
    page_order = pages.get("pageOrder", [])
    active_page_name = pages.get("activePageName")
    if not page_order:
        errors.append("pages.json: pageOrder must contain at least one page")
    elif active_page_name not in page_order:
        errors.append("pages.json: activePageName must be present in pageOrder")

    page_directories = sorted(
        path.name for path in PAGES_ROOT.iterdir() if path.is_dir()
    )
    if sorted(page_order) != page_directories:
        errors.append(
            "pages.json pageOrder differs from page directories: "
            f"order={sorted(page_order)}, directories={page_directories}"
        )

    for page_name in page_order:
        page = load_json(PAGES_ROOT / page_name / "page.json")
        if page.get("name") != page_name:
            errors.append(f"{page_name}/page.json: name must match its directory")
        for required_property in ("displayName", "displayOption", "width", "height"):
            if required_property not in page:
                errors.append(
                    f"{page_name}/page.json: missing {required_property}"
                )


def validate_tmdl(errors: list[str]) -> None:
    table_files = sorted(TABLE_ROOT.glob("*.tmdl"))
    table_names: set[str] = set()
    columns_by_table: dict[str, set[str]] = {}

    for table_file in table_files:
        text = table_file.read_text(encoding="utf-8")
        lines = text.splitlines()
        if any(line.startswith(" ") for line in lines if line):
            errors.append(f"{table_file.name}: indentation must start with tabs")

        table_match = next(
            (OBJECT_NAME_PATTERN.match(line) for line in lines if line.startswith("table ")),
            None,
        )
        if table_match is None:
            errors.append(f"{table_file.name}: missing table declaration")
            continue

        table_name = unquote_tmdl_name(table_match.group(1))
        if table_name != table_file.stem:
            errors.append(
                f"{table_file.name}: declaration {table_name!r} does not match filename"
            )

        table_names.add(table_name)
        columns_by_table[table_name] = {
            unquote_tmdl_name(match.group(1))
            for line in lines
            if (match := COLUMN_NAME_PATTERN.match(line))
        }

        if "\tpartition " not in text:
            errors.append(f"{table_file.name}: missing partition")

        validate_measure_formats(table_file.name, lines, errors)

    model_refs = {
        unquote_tmdl_name(match.group(1))
        for line in (DEFINITION_ROOT / "model.tmdl").read_text(encoding="utf-8").splitlines()
        if (match := MODEL_REF_PATTERN.match(line))
    }
    if model_refs != table_names:
        errors.append(
            "model.tmdl table references differ from table files: "
            f"missing={sorted(table_names - model_refs)}, extra={sorted(model_refs - table_names)}"
        )

    relationship_lines = (DEFINITION_ROOT / "relationships.tmdl").read_text(
        encoding="utf-8"
    ).splitlines()
    for line in relationship_lines:
        match = RELATIONSHIP_COLUMN_PATTERN.match(line)
        if match is None:
            continue
        table_name = unquote_tmdl_name(match.group(1))
        column_name = unquote_tmdl_name(match.group(2))
        if table_name not in columns_by_table:
            errors.append(f"relationships.tmdl: unknown table {table_name}")
        elif column_name not in columns_by_table[table_name]:
            errors.append(
                f"relationships.tmdl: unknown column {table_name}.{column_name}"
            )


def main() -> None:
    errors: list[str] = []
    validate_json_entry_points(errors)
    validate_report_definition(errors)
    validate_tmdl(errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)

    print("Power BI project structure is valid.")


if __name__ == "__main__":
    main()
