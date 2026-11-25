"""The planning sheet: an Excel version of the planning checklist.

Besides the checklist itself, the workbook has an "Individuals" and an
"Items" sheet. A study team fills these in while planning (age, sex, item
category, ...) and uploads the same file again when adding data to the
repository, so nothing has to be typed in twice.

Rows that already exist in the study carry their ID, so a re-upload updates
them instead of creating duplicates. Rows without an ID are created. Rows
removed from the sheet are left alone - nothing is ever deleted by an upload.

Choices (sex, categories, scenarios) are written and read by name; a hidden
"Lists" sheet feeds the dropdowns.
"""

from dataclasses import dataclass, field
from io import BytesIO
from tempfile import SpooledTemporaryFile
from typing import Any, Callable, Optional
from uuid import UUID

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter, quote_sheetname
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.worksheet import Worksheet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.determination_of_shedding_propensity_category import (
    DeterminationOfSheddingPropensityCategory,
)
from app.models.dna_shedding_propensity_category import DNASheddingPropensityCategory
from app.models.individual import Individual
from app.models.item import Item
from app.models.item_category import ItemCategory
from app.models.item_subcategory import ItemSubcategory
from app.models.scenario import Scenario
from app.models.sex import Sex
from app.models.skin_disease_category import SkinDiseaseCategory
from app.models.study import Study
from app.services.planning_checklist import get_progress, get_sections

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

INDIVIDUALS_SHEET = "Individuals"
ITEMS_SHEET = "Items"
LISTS_SHEET = "Lists"
SCENARIO_SEPARATOR = ";"
# Rows offered with dropdowns below the existing data.
EMPTY_ROWS = 200

INDIVIDUAL_HEADERS = [
    "ID",
    "Name / code",
    "Sex",
    "Age",
    "DNA shedding propensity",
    "Skin disease",
    "Determination of shedding propensity",
    "Scenarios",
]
ITEM_HEADERS = ["ID", "Category", "Subcategory", "Description", "Scenarios"]

_HEADER_FONT = Font(bold=True, color="FFFFFF")
_HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
_ID_FONT = Font(color="808080")


# --- Lookups ---------------------------------------------------------------


def _key(value: str) -> str:
    return " ".join(value.split()).casefold()


@dataclass
class _Choices:
    """Names shown in the sheet <-> record ids, for one dropdown."""

    labels: dict[UUID, str] = field(default_factory=dict)
    by_key: dict[str, list[UUID]] = field(default_factory=dict)

    def add(self, id: UUID, label: str) -> None:
        self.labels[id] = label
        self.by_key.setdefault(_key(label), []).append(id)

    def names(self) -> list[str]:
        return sorted(set(self.labels.values()), key=str.casefold)


def _named(records, label: Callable[[Any], Optional[str]]) -> _Choices:
    choices = _Choices()
    seen: dict[str, int] = {}
    for record in records:
        text = (label(record) or "").strip() or f"#{str(record.id)[:8]}"
        # Two records with the same label can't be told apart in a dropdown.
        count = seen.get(_key(text), 0)
        seen[_key(text)] = count + 1
        if count:
            text = f"{text} ({str(record.id)[:8]})"
        choices.add(record.id, text)
    return choices


@dataclass
class _Lookups:
    sex: _Choices
    dna_shedding: _Choices
    skin_disease: _Choices
    determination: _Choices
    item_category: _Choices
    subcategories: list[ItemSubcategory]
    scenarios: _Choices


async def _all(db: AsyncSession, model) -> list:
    return list((await db.execute(select(model))).scalars().all())


async def _lookups(db: AsyncSession, study: Study) -> _Lookups:
    return _Lookups(
        sex=_named(await _all(db, Sex), lambda r: r.name),
        dna_shedding=_named(await _all(db, DNASheddingPropensityCategory), lambda r: r.name),
        skin_disease=_named(await _all(db, SkinDiseaseCategory), lambda r: r.name),
        determination=_named(
            await _all(db, DeterminationOfSheddingPropensityCategory),
            lambda r: r.title or r.doi,
        ),
        item_category=_named(await _all(db, ItemCategory), lambda r: r.name),
        subcategories=await _all(db, ItemSubcategory),
        scenarios=_named(
            sorted(study.scenarios, key=lambda s: (s.name or "").casefold()), lambda r: r.name
        ),
    )


async def _study_individuals(db: AsyncSession, study: Study) -> list[Individual]:
    result = await db.execute(select(Individual).where(Individual.study_id == study.id))
    return sorted(result.scalars().all(), key=lambda i: ((i.name or "").casefold(), str(i.id)))


async def _study_items(db: AsyncSession, study: Study) -> list[Item]:
    result = await db.execute(select(Item).where(Item.studies.any(Study.id == study.id)))
    return list(result.scalars().all())


# --- Writing ---------------------------------------------------------------


def _header_row(ws: Worksheet, headers: list[str], widths: list[int]) -> None:
    ws.append(headers)
    for col, width in enumerate(widths, start=1):
        cell = ws.cell(row=1, column=col)
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.freeze_panes = "B2"


def _list_column(lists: Worksheet, col: int, title: str, values: list[str]) -> Optional[str]:
    """Write a dropdown's values to the hidden Lists sheet; return its range."""
    lists.cell(row=1, column=col, value=title).font = Font(bold=True)
    for row, value in enumerate(values, start=2):
        lists.cell(row=row, column=col, value=value)
    if not values:
        return None
    letter = get_column_letter(col)
    return f"{quote_sheetname(LISTS_SHEET)}!${letter}$2:${letter}${len(values) + 1}"


def _dropdown(
    ws: Worksheet,
    source: Optional[str],
    column: int,
    last_row: int,
    *,
    strict: bool = True,
    prompt: Optional[str] = None,
) -> None:
    if source is None:
        return
    validation = DataValidation(type="list", formula1=source, allow_blank=True)
    # Scenarios may list several names, which a list validation would reject.
    validation.showErrorMessage = strict
    if prompt:
        validation.promptTitle = ws.cell(row=1, column=column).value
        validation.prompt = prompt
        validation.showInputMessage = True
    letter = get_column_letter(column)
    validation.add(f"{letter}2:{letter}{last_row}")
    ws.add_data_validation(validation)


def _scenario_names(ids, lookups: _Lookups) -> str:
    names = [lookups.scenarios.labels[id] for id in ids if id in lookups.scenarios.labels]
    return f"{SCENARIO_SEPARATOR} ".join(sorted(names, key=str.casefold))


def _write_checklist(
    ws: Worksheet,
    study: Study,
    sections: list[dict],
    checked: list[str],
    notes: dict[str, str],
) -> None:
    ws["A1"] = "Planning checklist"
    ws["A1"].font = Font(bold=True, size=16)
    ws["A2"] = study.title or f"Study {study.id}"
    ws["A4"] = (
        "Enter the individuals and items you plan to use on the Individuals and Items sheets. "
        "When you add data to the repository, upload this file again under "
        "Data entry > Upload planning sheet."
    )
    ws["A4"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A4:C4")
    ws.row_dimensions[4].height = 45
    ws.column_dimensions["A"].width = 70
    ws.column_dimensions["B"].width = 10
    ws.column_dimensions["C"].width = 50

    done = DataValidation(type="list", formula1='"Yes,No,n/a"', allow_blank=True)
    ws.add_data_validation(done)
    row = 6
    for section in sections:
        title, items = section["title"], section["items"]
        ws.cell(row=row, column=1, value=title).font = Font(bold=True, size=13)
        ws.cell(row=row, column=2, value="Done").font = Font(bold=True)
        ws.cell(row=row, column=3, value="Notes").font = Font(bold=True)
        row += 1
        for item in items:
            ws.cell(row=row, column=1, value=item["text"]).alignment = Alignment(wrap_text=True)
            if item["id"] in checked:
                ws.cell(row=row, column=2, value="Yes")
            if notes.get(item["id"]):
                ws.cell(row=row, column=3, value=notes[item["id"]]).alignment = Alignment(wrap_text=True)
            done.add(f"B{row}")
            row += 1
        row += 1
    ws.cell(row=row, column=1, value="Notes").font = Font(bold=True, size=13)


async def build_planning_sheet(db: AsyncSession, study: Study) -> SpooledTemporaryFile:
    lookups = await _lookups(db, study)
    individuals = await _study_individuals(db, study)
    items = await _study_items(db, study)

    wb = Workbook()
    sections, _ = await get_sections(db, study.laboratory_id)
    checked, notes = await get_progress(db, study.id)
    _write_checklist(wb.active, study, sections, checked, notes)
    wb.active.title = "Checklist"

    lists = wb.create_sheet(LISTS_SHEET)
    lists.sheet_state = "hidden"
    sources = {
        "sex": _list_column(lists, 1, "Sex", lookups.sex.names()),
        "dna": _list_column(lists, 2, "DNA shedding propensity", lookups.dna_shedding.names()),
        "skin": _list_column(lists, 3, "Skin disease", lookups.skin_disease.names()),
        "det": _list_column(lists, 4, "Determination", lookups.determination.names()),
        "cat": _list_column(lists, 5, "Item category", lookups.item_category.names()),
        "sub": _list_column(
            lists,
            6,
            "Item subcategory",
            sorted({(s.name or "").strip() for s in lookups.subcategories} - {""}, key=str.casefold),
        ),
        "scen": _list_column(lists, 7, "Scenario", lookups.scenarios.names()),
    }
    scenario_prompt = (
        f"Pick a scenario, or type several separated by '{SCENARIO_SEPARATOR}'."
    )

    # Individuals
    ws = wb.create_sheet(INDIVIDUALS_SHEET, 1)
    _header_row(ws, INDIVIDUAL_HEADERS, [38, 18, 12, 8, 24, 24, 36, 36])
    for individual in individuals:
        ws.append([
            str(individual.id),
            individual.name,
            lookups.sex.labels.get(individual.sex_id),
            individual.age,
            lookups.dna_shedding.labels.get(individual.dna_shedding_propensity_category_id),
            lookups.skin_disease.labels.get(individual.skin_disease_category_id),
            lookups.determination.labels.get(
                individual.determination_of_shedding_propensity_category_id
            ),
            _scenario_names(individual.scenario_ids, lookups),
        ])
        ws.cell(row=ws.max_row, column=1).font = _ID_FONT
    last = len(individuals) + 1 + EMPTY_ROWS
    _dropdown(ws, sources["sex"], 3, last)
    age = DataValidation(type="whole", operator="between", formula1="0", formula2="150", allow_blank=True)
    age.error = "Please enter the age in whole years."
    age.add(f"D2:D{last}")
    ws.add_data_validation(age)
    _dropdown(ws, sources["dna"], 5, last)
    _dropdown(ws, sources["skin"], 6, last)
    _dropdown(ws, sources["det"], 7, last)
    _dropdown(ws, sources["scen"], 8, last, strict=False, prompt=scenario_prompt)

    # Items
    ws = wb.create_sheet(ITEMS_SHEET, 2)
    _header_row(ws, ITEM_HEADERS, [38, 24, 24, 40, 36])
    study_scenario_ids = set(lookups.scenarios.labels)
    for item in items:
        ws.append([
            str(item.id),
            lookups.item_category.labels.get(item.item_category_id),
            item.item_subcategory.name if item.item_subcategory else None,
            item.description,
            _scenario_names([id for id in item.scenario_ids if id in study_scenario_ids], lookups),
        ])
        ws.cell(row=ws.max_row, column=1).font = _ID_FONT
    last = len(items) + 1 + EMPTY_ROWS
    new_category_prompt = "Pick from the list, or type a new name - it is added when you upload the file."
    _dropdown(ws, sources["cat"], 2, last, strict=False, prompt=new_category_prompt)
    _dropdown(ws, sources["sub"], 3, last, strict=False, prompt=new_category_prompt)
    _dropdown(ws, sources["scen"], 5, last, strict=False, prompt=scenario_prompt)

    # Help
    help_ws = wb.create_sheet("How to use", 0)
    help_ws.column_dimensions["A"].width = 110
    for line in [
        "How to use this file",
        "",
        "1. While planning, add one row per individual on the Individuals sheet and one row per item on the Items sheet.",
        "2. Pick values from the dropdowns. Separate several scenarios with "
        f"'{SCENARIO_SEPARATOR}'. If the scenarios aren't planned yet, leave the column empty - "
        "you assign scenarios to these rows when uploading.",
        "   For items you can also type a new category or subcategory; you are asked to confirm it when uploading.",
        "3. Leave the ID column empty for new rows. Rows with an ID already exist in the repository and are updated.",
        "4. When you add data to the repository, open the study's Data entry step and upload this file "
        "with 'Upload planning sheet'.",
        "",
        "Removing a row from this file does not delete anything in the repository.",
        "Scenarios must be planned in the repository before they can be used here; "
        "download a fresh copy to get new scenarios in the dropdowns.",
    ]:
        help_ws.append([line])
    help_ws["A1"].font = Font(bold=True, size=14)
    # Open the file on the instructions.
    for sheet in wb.worksheets:
        sheet.sheet_view.tabSelected = sheet is help_ws
    wb.active = help_ws

    out = SpooledTemporaryFile(max_size=4 * 1024 * 1024)
    wb.save(out)
    out.seek(0)
    return out


# --- Reading ---------------------------------------------------------------


class PlanningSheetError(Exception):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


class NeedsConfirmationError(Exception):
    """The sheet is valid, but the user has to decide something first:

    - item categories/subcategories that don't exist yet (upload again with
      `create_categories` to create them), and/or
    - individuals/items without a scenario, e.g. because the study had no
      scenarios when the sheet was filled in (upload again with
      `default_scenario_ids` to assign them).
    """

    def __init__(
        self,
        categories: list[str],
        subcategories: list[dict[str, str]],
        unassigned_individuals: int,
        unassigned_items: int,
    ):
        super().__init__("The planning sheet needs confirmation.")
        self.categories = categories
        self.subcategories = subcategories
        self.unassigned_individuals = unassigned_individuals
        self.unassigned_items = unassigned_items


@dataclass
class ImportSummary:
    individuals_created: int = 0
    individuals_updated: int = 0
    items_created: int = 0
    items_updated: int = 0
    categories_created: int = 0
    subcategories_created: int = 0


def _text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    text = str(value).strip()
    return text or None


def _rows(ws: Worksheet, headers: list[str]) -> list[tuple[int, dict[str, Any]]]:
    header_cells = [_text(c.value) for c in next(ws.iter_rows(min_row=1, max_row=1))]
    columns: dict[str, int] = {}
    for header in headers:
        matches = [i for i, h in enumerate(header_cells) if h and _key(h) == _key(header)]
        if not matches:
            raise PlanningSheetError([f"{ws.title}: column '{header}' is missing."])
        columns[header] = matches[0]
    rows = []
    for number, cells in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        values = {h: (cells[i] if i < len(cells) else None) for h, i in columns.items()}
        if any(_text(v) is not None for v in values.values()):
            rows.append((number, values))
    return rows


class _RowReader:
    def __init__(self, sheet: str, number: int, values: dict[str, Any], errors: list[str]):
        self.sheet, self.number, self.values, self.errors = sheet, number, values, errors

    def error(self, message: str) -> None:
        self.errors.append(f"{self.sheet}, row {self.number}: {message}")

    def text(self, header: str) -> Optional[str]:
        return _text(self.values[header])

    def choice(self, header: str, choices: _Choices) -> Optional[UUID]:
        text = self.text(header)
        if text is None:
            return None
        ids = choices.by_key.get(_key(text), [])
        if len(ids) != 1:
            self.error(f"{header} '{text}' is not one of the available options.")
            return None
        return ids[0]

    def scenarios(self, header: str, choices: _Choices) -> list[UUID]:
        text = self.text(header)
        if text is None:
            return []
        ids: list[UUID] = []
        for name in text.replace(",", SCENARIO_SEPARATOR).split(SCENARIO_SEPARATOR):
            if not name.strip():
                continue
            matches = choices.by_key.get(_key(name), [])
            if len(matches) != 1:
                self.error(f"scenario '{name.strip()}' is not a scenario of this study.")
            elif matches[0] not in ids:
                ids.append(matches[0])
        return ids

    def id(self, known: dict[UUID, Any], what: str) -> Optional[UUID]:
        text = self.text("ID")
        if text is None:
            return None
        try:
            id = UUID(text)
        except ValueError:
            self.error(f"ID '{text}' is not valid. Leave the ID empty for new {what}.")
            return None
        if id not in known:
            self.error(f"ID '{text}' does not belong to this study. Leave the ID empty for new {what}.")
            return None
        return id


def _scenario_cell(reader: _RowReader, lookups: _Lookups) -> Optional[list[UUID]]:
    """The row's scenarios, or None if the cell is empty."""
    if reader.text("Scenarios") is None:
        return None
    return reader.scenarios("Scenarios", lookups.scenarios)


def _age(reader: _RowReader) -> Optional[int]:
    value = reader.values["Age"]
    if _text(value) is None:
        return None
    try:
        number = float(str(value).replace(",", "."))
    except ValueError:
        reader.error(f"Age '{value}' is not a number.")
        return None
    if not number.is_integer() or not 0 <= number <= 150:
        reader.error(f"Age '{value}' must be a whole number of years between 0 and 150.")
        return None
    return int(number)


async def apply_planning_sheet(
    db: AsyncSession,
    study: Study,
    content: bytes,
    *,
    create_categories: bool = False,
    default_scenario_ids: Optional[list[UUID]] = None,
) -> ImportSummary:
    """Create/update the study's individuals and items from an uploaded sheet.

    Every row is checked first; nothing is saved unless the whole file is valid.
    Item categories and subcategories that don't exist yet are only created
    with `create_categories`; otherwise NeedsConfirmationError lists them, so
    the user can check them for typos before they land in the shared catalog.

    Every individual and item needs a scenario. Rows without one (and that
    don't already have one) get `default_scenario_ids`; without those,
    NeedsConfirmationError reports how many rows need them.
    """
    try:
        wb = load_workbook(BytesIO(content), data_only=True, read_only=True)
    except Exception:
        raise PlanningSheetError(["This file could not be read. Please upload the .xlsx planning sheet."])

    missing = [name for name in (INDIVIDUALS_SHEET, ITEMS_SHEET) if name not in wb.sheetnames]
    if missing:
        raise PlanningSheetError(
            [f"The sheet '{name}' is missing. Please upload the planning sheet downloaded from the checklist." for name in missing]
        )

    lookups = await _lookups(db, study)
    individuals = {i.id: i for i in await _study_individuals(db, study)}
    items = {i.id: i for i in await _study_items(db, study)}
    scenarios = {s.id: s for s in study.scenarios}
    errors: list[str] = []

    individual_rows = _rows(wb[INDIVIDUALS_SHEET], INDIVIDUAL_HEADERS)
    item_rows = _rows(wb[ITEMS_SHEET], ITEM_HEADERS)
    wb.close()

    individual_changes = []
    seen_ids: set[UUID] = set()
    for number, values in individual_rows:
        r = _RowReader(INDIVIDUALS_SHEET, number, values, errors)
        id = r.id(individuals, "individuals")
        if id is not None:
            if id in seen_ids:
                r.error("this ID appears more than once.")
            seen_ids.add(id)
        data = dict(
            name=r.text("Name / code"),
            sex_id=r.choice("Sex", lookups.sex),
            age=_age(r),
            dna_shedding_propensity_category_id=r.choice("DNA shedding propensity", lookups.dna_shedding),
            skin_disease_category_id=r.choice("Skin disease", lookups.skin_disease),
            determination_of_shedding_propensity_category_id=r.choice(
                "Determination of shedding propensity", lookups.determination
            ),
        )
        individual_changes.append((id, data, _scenario_cell(r, lookups)))

    subcategories_by_category: dict[Optional[UUID], dict[str, list[ItemSubcategory]]] = {}
    for sub in lookups.subcategories:
        subcategories_by_category.setdefault(sub.item_category_id, {}).setdefault(
            _key(sub.name or ""), []
        ).append(sub)

    # A category is an existing id or the key of a new name; same for subcategories.
    CategoryRef = UUID | str
    new_categories: dict[str, str] = {}  # key -> name as first typed
    new_subcategories: dict[tuple[CategoryRef, str], str] = {}

    item_changes = []
    seen_ids = set()
    for number, values in item_rows:
        r = _RowReader(ITEMS_SHEET, number, values, errors)
        id = r.id(items, "items")
        if id is not None:
            if id in seen_ids:
                r.error("this ID appears more than once.")
            seen_ids.add(id)

        category: Optional[CategoryRef] = None
        category_text = r.text("Category")
        if category_text is not None:
            ids = lookups.item_category.by_key.get(_key(category_text), [])
            if len(ids) == 1:
                category = ids[0]
            elif len(ids) > 1:
                r.error(f"Category '{category_text}' matches several categories.")
            else:
                category = _key(category_text)
                new_categories.setdefault(category, " ".join(category_text.split()))

        subcategory: Optional[CategoryRef | tuple[CategoryRef, str]] = None
        sub_text = r.text("Subcategory")
        if sub_text is not None:
            if category_text is None:
                r.error("choose a category before a subcategory.")
            elif category is not None:
                existing = (
                    subcategories_by_category.get(category, {}).get(_key(sub_text), [])
                    if isinstance(category, UUID)
                    else []
                )
                if len(existing) == 1:
                    subcategory = existing[0].id
                elif len(existing) > 1:
                    r.error(f"Subcategory '{sub_text}' matches several subcategories.")
                else:
                    subcategory = (category, _key(sub_text))
                    new_subcategories.setdefault(subcategory, " ".join(sub_text.split()))

        data = dict(description=r.text("Description"))
        item_changes.append((id, data, category, subcategory, _scenario_cell(r, lookups)))

    default_scenarios = []
    for scenario_id in default_scenario_ids or []:
        if scenario_id not in scenarios:
            errors.append("The scenarios chosen for rows without a scenario must belong to this study.")
            break
        default_scenarios.append(scenarios[scenario_id])

    # An empty Scenarios cell keeps what an existing row already has; rows
    # that would end up without a scenario need the default ones.
    def has_scenarios(record) -> bool:
        return record is not None and any(s.id in scenarios for s in record.scenarios)

    unassigned_individuals = sum(
        1
        for id, _, scenario_ids in individual_changes
        if scenario_ids is None and not has_scenarios(individuals.get(id))
    )
    unassigned_items = sum(
        1
        for id, _, _, _, scenario_ids in item_changes
        if scenario_ids is None and not has_scenarios(items.get(id))
    )

    if errors:
        raise PlanningSheetError(errors)

    def category_name(ref: CategoryRef) -> str:
        return lookups.item_category.labels[ref] if isinstance(ref, UUID) else new_categories[ref]

    needs_categories = bool(new_categories or new_subcategories) and not create_categories
    needs_scenarios = bool(unassigned_individuals or unassigned_items) and not default_scenarios
    if needs_categories or needs_scenarios:
        raise NeedsConfirmationError(
            sorted(new_categories.values(), key=str.casefold) if needs_categories else [],
            sorted(
                (
                    {"category": category_name(category), "name": name}
                    for (category, _), name in new_subcategories.items()
                ),
                key=lambda entry: (entry["category"].casefold(), entry["name"].casefold()),
            )
            if needs_categories
            else [],
            unassigned_individuals if needs_scenarios else 0,
            unassigned_items if needs_scenarios else 0,
        )

    summary = ImportSummary()

    category_ids: dict[CategoryRef, UUID] = {}
    for key, name in new_categories.items():
        created = ItemCategory(name=name)
        db.add(created)
        await db.flush()
        category_ids[key] = created.id
        summary.categories_created += 1
    subcategory_ids: dict[tuple[CategoryRef, str], UUID] = {}
    for ref, name in new_subcategories.items():
        category_ref = ref[0]
        category_id = category_ref if isinstance(category_ref, UUID) else category_ids[category_ref]
        created = ItemSubcategory(name=name, item_category_id=category_id)
        db.add(created)
        await db.flush()
        subcategory_ids[ref] = created.id
        summary.subcategories_created += 1

    def resolve_category(ref: Optional[CategoryRef]) -> Optional[UUID]:
        if ref is None or isinstance(ref, UUID):
            return ref
        return category_ids[ref]

    def resolve_subcategory(ref) -> Optional[UUID]:
        if ref is None or isinstance(ref, UUID):
            return ref
        return subcategory_ids[ref]

    def linked_scenarios(scenario_ids: Optional[list[UUID]], record) -> Optional[list]:
        """The study scenarios to link, or None to keep the record's own."""
        if scenario_ids is not None:
            return [scenarios[s] for s in scenario_ids]
        if has_scenarios(record):
            return None
        return list(default_scenarios)

    for id, data, scenario_ids in individual_changes:
        linked = linked_scenarios(scenario_ids, individuals.get(id))
        if id is None:
            db.add(Individual(study_id=study.id, scenarios=linked, **data))
            summary.individuals_created += 1
        else:
            individual = individuals[id]
            for name, value in data.items():
                setattr(individual, name, value)
            if linked is not None:
                individual.scenarios = linked
            summary.individuals_updated += 1

    for id, data, category, subcategory, scenario_ids in item_changes:
        data = dict(
            data,
            item_category_id=resolve_category(category),
            item_subcategory_id=resolve_subcategory(subcategory),
        )
        linked = linked_scenarios(scenario_ids, items.get(id))
        if id is None:
            db.add(Item(studies=[study], scenarios=linked, **data))
            summary.items_created += 1
        else:
            item = items[id]
            for name, value in data.items():
                setattr(item, name, value)
            if linked is not None:
                # Keep links to other studies' scenarios; the sheet only lists this study's.
                item.scenarios = [s for s in item.scenarios if s.id not in scenarios] + linked
            summary.items_updated += 1

    await db.commit()
    return summary
