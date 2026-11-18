"""The catalog of downloadable data: datasets and the fields (columns) each
one offers.

A *dataset* fixes the row grain of a download (one row per result, per PCR,
per contact, ...) as a whitelisted SQL join over the domain model. A *field*
is a column a user may pick or filter on; it carries the SQL expression that
produces it. Data models only ever reference datasets and fields by key, so
user input never reaches SQL as raw text.

Conventions used throughout:

* Lookup tables (categories, kits, devices, ...) are exported by `name`,
  via scalar subqueries so the row joins stay small.
* Contacts and surfaces override their template's values when set; those
  fields are exported as ``COALESCE(instance.x, template.x)``.
* Many-to-many links (a contact template in several scenarios, a scenario
  with several persistencies, a surface with several DNA sources) are
  exported as ``"A; B"`` strings so they never duplicate rows.
* Durations are exported in seconds.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field as dc_field
from typing import Callable, Iterable, Literal, Optional

from sqlalchemy import (
    Float,
    String,
    and_,
    case,
    cast,
    distinct,
    func,
    literal_column,
    or_,
    select,
)
from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlalchemy.orm import aliased, join, outerjoin
from sqlalchemy.sql.elements import ColumnElement

from app.models.activity_category import ActivityCategory
from app.models.application_analytical_threshold import ApplicationAnalyticalThreshold
from app.models.author import Author
from app.models.body_part_condition_category import BodyPartConditionCategory
from app.models.ce_device import CEDevice
from app.models.ce_method import CEMethod
from app.models.condition_during_contact import ConditionDuringContact
from app.models.condition_of_item_part_category import ConditionOfItemPartCategory
from app.models.contact import Contact
from app.models.contact_template import ContactTemplate, scenario_contact_template
from app.models.degradation_category import DegradationCategory
from app.models.determination_of_shedding_propensity_category import (
    DeterminationOfSheddingPropensityCategory,
)
from app.models.disturbance_category import DisturbanceCategory
from app.models.dna_shedding_propensity_category import DNASheddingPropensityCategory
from app.models.dye_set import DyeSet
from app.models.epg_analysis_method import EPGAnalysisMethod
from app.models.epg_interpretation_method import EPGInterpretationMethod
from app.models.experience_level import ExperienceLevel
from app.models.extraction_method import ExtractionMethod
from app.models.friction_applied_estimate import FrictionAppliedEstimate
from app.models.genotyping_software import GenotypingSoftware
from app.models.geographic_location_category import GeographicLocationCategory
from app.models.individual import Individual, individual_scenario
from app.models.inhibition_category import InhibitionCategory
from app.models.item import Item
from app.models.item_category import ItemCategory
from app.models.item_parts_category import ItemPartsCategory
from app.models.item_subcategory import ItemSubcategory
from app.models.item_surface_material_category import ItemSurfaceMaterialCategory
from app.models.laboratory import Laboratory
from app.models.location_of_body_category import LocationOfBodyCategory
from app.models.pcr import PCR
from app.models.pcr_contributor import PCRContributor
from app.models.pcr_kit import PCRKit
from app.models.pcr_method import PCRMethod
from app.models.persistence import Persistence
from app.models.platform import Platform
from app.models.polymer import Polymer
from app.models.post_pcr_treatment_method import PostPCRTreatmentMethod
from app.models.pressure_estimate import PressureEstimate
from app.models.principle_of_extraction_method_category import (
    PrincipleOfExtractionMethodCategory,
)
from app.models.principle_of_quant_method_category import PrincipleOfQuantMethodCategory
from app.models.quantification_kit import QuantificationKit
from app.models.quantification_method import QuantificationMethod
from app.models.quantification_platform import QuantificationPlatform
from app.models.result import Result
from app.models.sample import Sample
from app.models.sample_set import SampleSet
from app.models.sampling_method import SamplingMethod
from app.models.scenario import Scenario, scenario_persistence, study_scenario
from app.models.scenario_category import ScenarioCategory
from app.models.sex import Sex
from app.models.size_standard import SizeStandard
from app.models.skin_disease_category import SkinDiseaseCategory
from app.models.source_of_dna_category import SourceOfDNACategory
from app.models.statistical_software import StatisticalSoftware
from app.models.study import Study
from app.models.study_author import StudyAuthor
from app.models.stutter_filter import StutterFilter
from app.models.surface import Surface, surface_source_of_dna
from app.models.surface_material_category import SurfaceMaterialCategory
from app.models.surface_template import SurfaceTemplate
from app.models.swab_method import SwabMethod
from app.models.swabbing_technique_category import SwabbingTechniqueCategory
from app.models.tape_method import TapeMethod
from app.models.thermocycler import Thermocycler
from app.models.type_of_swab_category import TypeOfSwabCategory
from app.models.type_of_tape import TypeOfTape
from app.models.wetting_agent import WettingAgent

FieldType = Literal["string", "category", "number", "boolean", "date"]

SEPARATOR = "; "


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    # The table the field belongs to, by label (see `Table`).
    group: str
    type: FieldType
    expr: ColumnElement
    description: Optional[str] = None
    unit: Optional[str] = None

    @property
    def table(self) -> str:
        return table_key(self.group)


def table_key(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")


@dataclass(frozen=True)
class Table:
    """A table a data model can join onto its rows. Its fields carry the
    table's label as their `group`."""

    key: str
    label: str
    description: str
    # Outer joins that bring the table in, as (target, on-clause) pairs.
    # Tables whose fields are subqueries need none.
    joins: tuple = ()
    # Tables that must be joined first.
    requires: tuple[str, ...] = ()
    # Always joined: the row's own table and the path to its study.
    required: bool = False


def table(
    label: str,
    description: str,
    joins: tuple = (),
    *,
    requires: tuple[str, ...] = (),
    required: bool = False,
) -> Table:
    return Table(
        key=table_key(label),
        label=label,
        description=description,
        joins=joins,
        requires=tuple(table_key(r) for r in requires),
        required=required,
    )


@dataclass
class Dataset:
    key: str
    label: str
    description: str
    # The FROM clause of every query: the row's table plus the joins of
    # all required tables.
    base: object
    # In join order: a table comes after the tables it requires.
    tables: list[Table]
    # The id of the study each row belongs to. Visibility and the study
    # scope of a data model are both enforced on this expression, so it
    # may only use required tables.
    study_id: ColumnElement
    # A unique, stable expression to break sort ties with.
    row_id: ColumnElement
    default_sort: list[str]
    fields: list[Field] = dc_field(default_factory=list)

    def __post_init__(self) -> None:
        self._by_key = {f.key: f for f in self.fields}
        if len(self._by_key) != len(self.fields):
            seen: set[str] = set()
            dupes = [f.key for f in self.fields if f.key in seen or seen.add(f.key)]
            raise ValueError(f"Duplicate field keys in dataset {self.key}: {dupes}")
        self._tables = {t.key: t for t in self.tables}
        missing = {f.group for f in self.fields if f.table not in self._tables}
        if missing:
            raise ValueError(f"Dataset {self.key} has fields without a table: {missing}")
        for position, t in enumerate(self.tables):
            earlier = {e.key for e in self.tables[:position]}
            if not set(t.requires) <= earlier:
                raise ValueError(f"Table {t.key} of {self.key} must come after {t.requires}")

    def get(self, key: str) -> Optional[Field]:
        return self._by_key.get(key)

    def get_table(self, key: str) -> Optional[Table]:
        return self._tables.get(key)

    def resolve_tables(self, keys: Iterable[str]) -> list[Table]:
        """The given tables plus everything they require and every required
        table, in join order. Unknown keys raise KeyError."""
        wanted = {t.key for t in self.tables if t.required}
        pending = list(keys)
        while pending:
            key = pending.pop()
            if key in wanted:
                continue
            t = self._tables[key]
            wanted.add(key)
            pending.extend(t.requires)
        return [t for t in self.tables if t.key in wanted]

    def from_clause(self, tables: Iterable[Table]):
        from_ = self.base
        for t in tables:
            if t.required:
                continue
            for target, onclause in t.joins:
                from_ = outerjoin(from_, target, onclause)
        return from_


# --- Expression helpers -----------------------------------------------------


def lookup(model, id_expr, column: str = "name") -> ColumnElement:
    """The `column` (default `name`) of the `model` row `id_expr` points at.

    Uses a fresh alias so the subquery never correlates to a table that
    happens to be in the outer FROM clause."""
    alias = aliased(model)
    return (
        select(getattr(alias, column))
        .where(alias.id == id_expr)
        .scalar_subquery()
    )


def seconds(interval_expr) -> ColumnElement:
    return cast(func.extract("epoch", interval_expr), Float)


def string_agg(value) -> ColumnElement:
    """``string_agg(DISTINCT value, '; ' ORDER BY value)``."""
    return func.string_agg(
        distinct(value), aggregate_order_by(literal_column(f"'{SEPARATOR}'"), value)
    )


def _row_scenarios(contact_template_id, study_id):
    """The scenarios a row belongs to: those using the row's contact
    template, limited to the row's study (a template may be shared by
    scenarios of other studies).

    The study link is joined rather than checked with a nested subquery:
    SQLAlchemy only correlates a subquery to its immediately enclosing
    SELECT, so a nested one wouldn't see the outer row's study."""
    sc = aliased(Scenario)
    link = study_scenario.alias()
    return sc, (
        select()
        .select_from(sc)
        .join(scenario_contact_template, scenario_contact_template.c.scenario_id == sc.id)
        .outerjoin(link, and_(link.c.scenario_id == sc.id, link.c.study_id == study_id))
        .where(scenario_contact_template.c.contact_template_id == contact_template_id)
        .where(or_(sc.owning_study_id == study_id, link.c.scenario_id.is_not(None)))
    )


def scenario_fields(contact_template_id, study_id, *, group="Scenario") -> list[Field]:
    def scenario_value(value_fn) -> ColumnElement:
        sc, base = _row_scenarios(contact_template_id, study_id)
        return base.add_columns(string_agg(value_fn(sc))).scalar_subquery()

    def category_value() -> ColumnElement:
        sc, base = _row_scenarios(contact_template_id, study_id)
        cat = aliased(ScenarioCategory)
        return (
            base.join(cat, cat.id == sc.scenario_category_id)
            .add_columns(string_agg(cat.name))
            .scalar_subquery()
        )

    def persistence_value(value_fn) -> ColumnElement:
        sc, base = _row_scenarios(contact_template_id, study_id)
        p = aliased(Persistence)
        return (
            base.join(scenario_persistence, scenario_persistence.c.scenario_id == sc.id)
            .join(p, p.id == scenario_persistence.c.persistence_id)
            .add_columns(string_agg(cast(value_fn(p), String)))
            .scalar_subquery()
        )

    def persistence_lookup(model, attr: str) -> ColumnElement:
        sc, base = _row_scenarios(contact_template_id, study_id)
        p = aliased(Persistence)
        m = aliased(model)
        return (
            base.join(scenario_persistence, scenario_persistence.c.scenario_id == sc.id)
            .join(p, p.id == scenario_persistence.c.persistence_id)
            .join(m, m.id == getattr(p, attr))
            .add_columns(string_agg(m.name))
            .scalar_subquery()
        )

    pgroup = "Persistence"
    return [
        Field("scenario.name", "Scenario", group, "category", scenario_value(lambda s: s.name)),
        Field("scenario.category", "Scenario category", group, "category", category_value()),
        Field(
            "scenario.realistic",
            "Realistic scenario",
            group,
            "category",
            scenario_value(lambda s: case((s.realistic, "yes"), else_="no")),
        ),
        Field("persistence.name", "Persistence", pgroup, "string", persistence_value(lambda p: p.name)),
        Field(
            "persistence.interval",
            "Interval of persistence",
            pgroup,
            "string",
            persistence_value(lambda p: p.interval_of_persistence),
        ),
        Field("persistence.temperature", "Temperature", pgroup, "string", persistence_value(lambda p: p.temperature), unit="°C"),
        Field("persistence.humidity", "Humidity", pgroup, "string", persistence_value(lambda p: p.humidity), unit="%"),
        Field("persistence.uv_irradiation", "UV irradiation", pgroup, "string", persistence_value(lambda p: p.uv_irradiation)),
        Field(
            "persistence.indoors",
            "Indoors",
            pgroup,
            "category",
            persistence_value(lambda p: case((p.indoors, "yes"), (p.indoors.is_(False), "no"))),
        ),
        Field(
            "persistence.geographic_location",
            "Geographic location",
            pgroup,
            "category",
            persistence_lookup(GeographicLocationCategory, "geographic_location_category_id"),
        ),
        Field(
            "persistence.disturbance",
            "Disturbance",
            pgroup,
            "category",
            persistence_lookup(DisturbanceCategory, "disturbance_category_id"),
        ),
    ]


def study_fields(st, lab) -> list[Field]:
    g = "Study"
    sa = aliased(StudyAuthor)
    au = aliased(Author)
    author_name = func.concat_ws(" ", au.first_name, au.last_name)
    authors = (
        select(
            func.string_agg(
                author_name, aggregate_order_by(literal_column("', '"), sa.position)
            )
        )
        .select_from(sa)
        .join(au, au.id == sa.author_id)
        .where(sa.study_id == st.id)
        .scalar_subquery()
    )
    return [
        Field("study.id", "Study ID", g, "string", cast(st.id, String)),
        Field("study.title", "Study title", g, "category", st.title),
        Field("study.authors", "Authors", g, "string", authors),
        Field("study.year", "Year", g, "category", st.year),
        Field("study.journal", "Journal", g, "category", st.journal),
        Field("study.doi", "DOI", g, "string", st.doi),
        Field("study.published", "Published", g, "boolean", st.published),
        Field("study.quality_check_passed", "Quality check passed", g, "boolean", st.quality_check_passed),
        Field("study.created_at", "Created", g, "date", st.created_at),
        Field("laboratory.name", "Laboratory", "Laboratory", "category", lab.laboratory_name),
        Field("laboratory.institution", "Institution", "Laboratory", "category", lab.institutional_affiliation),
        Field("laboratory.country", "Country", "Laboratory", "category", lab.country),
        Field("laboratory.city", "City", "Laboratory", "category", lab.city),
    ]


def individual_fields(ind, prefix: str, group: str, label_prefix: str = "") -> list[Field]:
    lp = label_prefix
    return [
        Field(f"{prefix}.id", f"{lp}Individual ID", group, "string", cast(ind.id, String)),
        Field(f"{prefix}.name", f"{lp}Individual", group, "category", ind.name),
        Field(f"{prefix}.sex", f"{lp}Sex", group, "category", lookup(Sex, ind.sex_id)),
        Field(f"{prefix}.age", f"{lp}Age", group, "number", ind.age, unit="years"),
        Field(
            f"{prefix}.shedding_propensity",
            f"{lp}DNA shedding propensity",
            group,
            "category",
            lookup(DNASheddingPropensityCategory, ind.dna_shedding_propensity_category_id),
        ),
        Field(
            f"{prefix}.shedding_propensity_determination",
            f"{lp}Determination of shedding propensity",
            group,
            "category",
            lookup(
                DeterminationOfSheddingPropensityCategory,
                ind.determination_of_shedding_propensity_category_id,
                "title",
            ),
        ),
        Field(
            f"{prefix}.skin_disease",
            f"{lp}Skin disease",
            group,
            "category",
            lookup(SkinDiseaseCategory, ind.skin_disease_category_id),
        ),
    ]


def surface_fields(su, sut, it, ind, prefix: str, group: str) -> list[Field]:
    """Fields describing one surface, resolving surface-over-template
    overrides. `su` is a Surface alias joined with its template `sut`, the
    template's item `it` and the surface's individual `ind`."""

    def resolved(attr: str):
        return func.coalesce(getattr(su, attr), getattr(sut, attr))

    body_location = lookup(LocationOfBodyCategory, resolved("location_of_body_category_id"))
    item_category = lookup(ItemCategory, it.item_category_id)
    item_part = lookup(ItemPartsCategory, resolved("item_parts_category_id"))

    src = aliased(SourceOfDNACategory)
    sources = (
        select(string_agg(src.name))
        .select_from(surface_source_of_dna)
        .join(src, src.id == surface_source_of_dna.c.source_of_dna_category_id)
        .where(surface_source_of_dna.c.surface_id == su.id)
        .scalar_subquery()
    )

    lp = f"{group}: "
    return [
        Field(f"{prefix}.id", f"{lp}Surface ID", group, "string", cast(su.id, String)),
        Field(
            f"{prefix}.kind",
            f"{lp}Kind",
            group,
            "category",
            case(
                (sut.item_id.is_not(None), "item"),
                (or_(su.individual_id.is_not(None), resolved("location_of_body_category_id").is_not(None)), "body"),
            ),
            description="Whether the surface is part of an item or of a person's body.",
        ),
        Field(
            f"{prefix}.label",
            group,
            group,
            "string",
            func.nullif(func.concat_ws(" · ", ind.name, body_location, item_category, item_part), ""),
            description="A readable summary of the surface: individual, body location, item and part.",
        ),
        *individual_fields(ind, f"{prefix}.individual", group, lp),
        Field(f"{prefix}.body_location", f"{lp}Body location", group, "category", body_location),
        Field(
            f"{prefix}.body_part_condition",
            f"{lp}Body part condition",
            group,
            "category",
            lookup(BodyPartConditionCategory, resolved("body_part_condition_category_id")),
        ),
        Field(f"{prefix}.item_category", f"{lp}Item category", group, "category", item_category),
        Field(
            f"{prefix}.item_subcategory",
            f"{lp}Item subcategory",
            group,
            "category",
            lookup(ItemSubcategory, it.item_subcategory_id),
        ),
        Field(f"{prefix}.item_description", f"{lp}Item description", group, "string", it.description),
        Field(f"{prefix}.item_part", f"{lp}Item part", group, "category", item_part),
        Field(
            f"{prefix}.item_part_condition",
            f"{lp}Item part condition",
            group,
            "category",
            lookup(ConditionOfItemPartCategory, resolved("condition_of_item_part_category_id")),
        ),
        Field(
            f"{prefix}.surface_material",
            f"{lp}Surface material",
            group,
            "category",
            lookup(SurfaceMaterialCategory, resolved("surface_material_category_id")),
        ),
        Field(
            f"{prefix}.item_surface_material",
            f"{lp}Item surface material",
            group,
            "category",
            lookup(ItemSurfaceMaterialCategory, resolved("item_surface_material_category_id")),
        ),
        Field(f"{prefix}.source_of_dna", f"{lp}Source of DNA", group, "string", sources),
        Field(f"{prefix}.background_dna", f"{lp}Background DNA", group, "boolean", sut.background_dna),
        Field(f"{prefix}.prevalence", f"{lp}Prevalence", group, "boolean", sut.prevalence),
    ]


def condition_fields(condition_id) -> list[Field]:
    """The environment a contact took place in."""
    g = "Conditions during contact"

    def value(attr: str):
        return lookup(ConditionDuringContact, condition_id, attr)

    def via(model, attr: str):
        # One subquery with a join; a lookup nested in a lookup wouldn't
        # correlate to the outer row (see _row_scenarios).
        cdc = aliased(ConditionDuringContact)
        m = aliased(model)
        return (
            select(m.name)
            .select_from(cdc)
            .join(m, m.id == getattr(cdc, attr))
            .where(cdc.id == condition_id)
            .scalar_subquery()
        )

    return [
        Field("contact_condition.temperature", "Temperature", g, "number", value("temperature"), unit="°C"),
        Field("contact_condition.humidity", "Humidity", g, "number", value("humidity"), unit="%"),
        Field("contact_condition.uv_irradiation", "UV irradiation", g, "number", value("uv_irradiation")),
        Field("contact_condition.indoors", "Indoors", g, "boolean", value("indoors")),
        Field("contact_condition.change_over_time", "Change over time", g, "boolean", value("change_over_time")),
        Field(
            "contact_condition.geographic_location",
            "Geographic location",
            g,
            "category",
            via(GeographicLocationCategory, "geographic_location_category_id"),
        ),
        Field(
            "contact_condition.disturbance",
            "Disturbance",
            g,
            "category",
            via(DisturbanceCategory, "disturbance_category_id"),
        ),
    ]


def contact_fields(co, cot, group: str = "Contact") -> list[Field]:
    def resolved(attr: str):
        return func.coalesce(getattr(co, attr), getattr(cot, attr))

    prev = aliased(Contact)
    prev_template = aliased(ContactTemplate)
    previous_name = (
        select(func.coalesce(prev.name, prev_template.name))
        .select_from(prev)
        .outerjoin(prev_template, prev_template.id == prev.contact_template_id)
        .where(prev.id == co.previous_contact_id)
        .scalar_subquery()
    )
    return [
        Field("contact.id", "Contact ID", group, "string", cast(co.id, String)),
        Field("contact.name", "Contact", group, "string", func.coalesce(co.name, cot.name)),
        Field("contact.template", "Planned contact", group, "category", cot.name),
        Field(
            "contact.previous",
            "Previous contact in chain",
            group,
            "string",
            previous_name,
            description="The contact this one directly follows; empty for the first contact of a chain.",
        ),
        Field("contact.duration", "Duration", group, "number", seconds(resolved("duration")), unit="s"),
        Field("contact.pressure", "Pressure", group, "number", co.pressure),
        Field(
            "contact.pressure_estimate",
            "Pressure estimate",
            group,
            "category",
            lookup(PressureEstimate, resolved("pressure_estimate_id")),
        ),
        Field("contact.friction_applied", "Friction applied", group, "number", co.friction_applied),
        Field(
            "contact.friction_applied_estimate",
            "Friction estimate",
            group,
            "category",
            lookup(FrictionAppliedEstimate, resolved("friction_applied_estimate_id")),
        ),
        Field("contact.area", "Contact area", group, "number", resolved("contact_area")),
        Field("contact.description", "Description of contact", group, "string", resolved("description_of_contact")),
        Field(
            "contact.activity",
            "Activity",
            group,
            "category",
            lookup(ActivityCategory, resolved("activity_category_id")),
        ),
        *condition_fields(resolved("condition_during_contact_id")),
    ]


def _surface_table(
    label: str, description: str, surface_id_expr, prefix: str, *, requires: tuple[str, ...] = ()
) -> tuple[Table, list[Field]]:
    """A surface with its template, item and individual, as a joinable table."""
    su = aliased(Surface)
    sut = aliased(SurfaceTemplate)
    it = aliased(Item)
    ind = aliased(Individual)
    joins = (
        (su, su.id == surface_id_expr),
        (sut, sut.id == su.surface_template_id),
        (it, it.id == sut.item_id),
        (ind, ind.id == su.individual_id),
    )
    return (
        table(label, description, joins, requires=requires),
        surface_fields(su, sut, it, ind, prefix=prefix, group=label),
    )


# --- Sample context, shared by the result, PCR and contributor datasets ------


@dataclass
class _SampleContext:
    base: object
    study: object
    tables: list[Table]
    fields: list[Field]


def _sample_context(from_, sm) -> _SampleContext:
    """Everything describing a sample, as tables joinable onto `from_`,
    which must already contain the Sample alias `sm`."""
    st = aliased(Study)
    lab = aliased(Laboratory)
    co = aliased(Contact)
    cot = aliased(ContactTemplate)
    smm = aliased(SamplingMethod)
    swab = aliased(SwabMethod)
    tape = aliased(TapeMethod)
    ext = aliased(ExtractionMethod)

    base = from_.join(st, st.id == sm.study_id)

    sampled_table, sampled_fields = _surface_table(
        "Sampled surface",
        "The surface the sample was taken from, with its item or individual.",
        sm.surface_id,
        "sampled_surface",
    )
    donor_table, donor_fields = _surface_table(
        "Donor surface",
        "The surface DNA was transferred from in the sample's contact.",
        co.donor_surface_id,
        "donor_surface",
        requires=("Contact",),
    )
    recipient_table, recipient_fields = _surface_table(
        "Recipient surface",
        "The surface DNA was transferred to in the sample's contact.",
        co.recipient_surface_id,
        "recipient_surface",
        requires=("Contact",),
    )
    tables = [
        table("Sample", "The sample the row belongs to.", required=True),
        table("Study", "The study the data comes from.", required=True),
        table(
            "Laboratory",
            "The laboratory that conducted the study.",
            ((lab, lab.id == st.laboratory_id),),
        ),
        table(
            "Sampling method",
            "How the sample was taken: technique, swab, wetting agent, tape.",
            (
                (smm, smm.id == sm.sampling_method_id),
                (swab, swab.id == smm.swab_method_id),
                (tape, tape.id == smm.tape_method_id),
            ),
        ),
        table(
            "Extraction method",
            "How DNA was extracted from the sample.",
            ((ext, ext.id == sm.extraction_method_id),),
        ),
        table(
            "Contact",
            "The contact the sample was taken after: duration, pressure, friction, activity.",
            ((co, co.id == sm.contact_id), (cot, cot.id == co.contact_template_id)),
        ),
        table(
            "Conditions during contact",
            "Temperature, humidity and location during the contact.",
            requires=("Contact",),
        ),
        table(
            "Scenario",
            "The scenario of the contact, within the row's study.",
            requires=("Contact",),
        ),
        table(
            "Persistence",
            "Persistence settings of the scenario (time, temperature, humidity, …).",
            requires=("Contact",),
        ),
        sampled_table,
        donor_table,
        recipient_table,
    ]

    sg = "Sample"
    mg = "Sampling method"
    eg = "Extraction method"
    sampling_kind = case(
        (smm.swab_method_id.is_not(None), "swab"),
        (smm.tape_method_id.is_not(None), "tape"),
        (smm.vacuum_method_id.is_not(None), "vacuum"),
        (smm.cutting_method_id.is_not(None), "cutting"),
        (smm.scraping_method_id.is_not(None), "scraping"),
        (smm.picking_method_id.is_not(None), "picking"),
    )
    fields = [
        *study_fields(st, lab),
        *scenario_fields(cot.id, st.id),
        Field("sample.id", "Sample ID", sg, "string", cast(sm.id, String)),
        Field("sample.name", "Sample", sg, "string", sm.name),
        Field("sample.set", "Sample set", sg, "category", lookup(SampleSet, sm.sample_set_id)),
        Field("sample.area", "Sampled area", sg, "number", sm.area),
        Field("sample.elution_volume", "Elution volume", sg, "number", sm.elution_volume, unit="µl"),
        Field(
            "sample.sampler_experience",
            "Experience level of sampler",
            sg,
            "category",
            lookup(ExperienceLevel, sm.experience_level_of_sampler_id),
        ),
        Field("sampling_method.id", "Sampling method ID", mg, "string", cast(smm.id, String)),
        Field("sampling_method.kind", "Sampling technique", mg, "category", sampling_kind),
        Field("sampling_method.swab_type", "Type of swab", mg, "category", lookup(TypeOfSwabCategory, swab.type_of_swab_category_id)),
        Field(
            "sampling_method.swabbing_technique",
            "Swabbing technique",
            mg,
            "category",
            lookup(SwabbingTechniqueCategory, swab.swabbing_technique_category_id),
        ),
        Field("sampling_method.wetting_agent", "Wetting agent", mg, "category", lookup(WettingAgent, swab.wetting_agent_id)),
        Field("sampling_method.wetting_agent_volume", "Volume of wetting agent", mg, "number", swab.volume_of_wetting_agent),
        Field("sampling_method.tape_type", "Type of tape", mg, "category", lookup(TypeOfTape, tape.type_of_tape_id)),
        Field("extraction_method.id", "Extraction method ID", eg, "string", cast(ext.id, String)),
        Field(
            "extraction_method.principle",
            "Extraction principle",
            eg,
            "category",
            lookup(PrincipleOfExtractionMethodCategory, ext.principle_of_extraction_method_category_id),
        ),
        Field("extraction_method.protocol", "Extraction protocol", eg, "string", ext.extraction_protocol),
        Field("extraction_method.platform", "Extraction platform", eg, "category", lookup(Platform, ext.extraction_platform_id)),
        Field("extraction_method.lysis_time", "Lysis incubation time", eg, "number", seconds(ext.lysis_incubation_time), unit="s"),
        Field("extraction_method.lysis_temperature", "Lysis incubation temperature", eg, "number", ext.lysis_incubation_temperature, unit="°C"),
        Field(
            "extraction_method.lysate_volume",
            "Volume of lysate used for extraction",
            eg,
            "number",
            ext.volume_of_lysate_used_for_extraction,
            unit="µl",
        ),
        Field(
            "extraction_method.further_purification",
            "Further purification step",
            eg,
            "boolean",
            ext.application_of_further_purification_step,
        ),
        *contact_fields(co, cot),
        Field(
            "sample.surface_role",
            "Sampled surface role",
            "Contact",
            "category",
            case(
                (co.recipient_surface_id == sm.surface_id, "recipient"),
                (co.donor_surface_id == sm.surface_id, "donor"),
            ),
            description="Whether the sample was taken from the donor or the recipient surface of its contact.",
        ),
        *sampled_fields,
        *donor_fields,
        *recipient_fields,
    ]
    return _SampleContext(base=base, study=st, tables=tables, fields=fields)


def _result_tables(res) -> tuple[list[Table], list[Field]]:
    """The quantification method of a result, as a joinable table."""
    qm = aliased(QuantificationMethod)
    tables = [
        table(
            "Quantification method",
            "How the DNA was quantified: principle, kit, platform.",
            ((qm, qm.id == res.quantification_method_id),),
        )
    ]
    return tables, _result_fields(res, qm)


def _result_fields(res, qm) -> list[Field]:
    g = "Result"
    qg = "Quantification method"
    return [
        Field("result.id", "Result ID", g, "string", cast(res.id, String)),
        Field("result.dna_concentration", "DNA concentration", g, "number", res.dna_concentration, unit="ng/µl"),
        Field("result.degradation", "Degradation", g, "category", lookup(DegradationCategory, res.degradation_category_id)),
        Field("result.inhibition", "Inhibition", g, "category", lookup(InhibitionCategory, res.inhibition_category_id)),
        Field("quantification_method.id", "Quantification method ID", qg, "string", cast(qm.id, String)),
        Field(
            "quantification_method.principle",
            "Quantification principle",
            qg,
            "category",
            lookup(PrincipleOfQuantMethodCategory, qm.principle_of_quant_method_category_id),
        ),
        Field("quantification_method.kit", "Quantification kit", qg, "category", lookup(QuantificationKit, qm.kit_id)),
        Field("quantification_method.platform", "Quantification platform", qg, "category", lookup(QuantificationPlatform, qm.platform_id)),
    ]


def _pcr_tables(pcr) -> tuple[list[Table], list[Field]]:
    """The methods of a PCR, as joinable tables."""
    pm = aliased(PCRMethod)
    ce = aliased(CEMethod)
    epa = aliased(EPGAnalysisMethod)
    epi = aliased(EPGInterpretationMethod)
    post = aliased(PostPCRTreatmentMethod)
    tables = [
        table(
            "PCR method",
            "PCR kit, thermocycler and cycling, plus post-PCR treatment.",
            (
                (pm, pm.id == pcr.pcr_method_id),
                (post, post.id == pcr.post_pcr_treatment_method_id),
            ),
        ),
        table("CE method", "Capillary electrophoresis settings.", ((ce, ce.id == pcr.ce_method_id),)),
        table(
            "EPG analysis",
            "Genotyping software, analytical threshold, stutter filter.",
            ((epa, epa.id == pcr.epg_analysis_method_id),),
        ),
        table(
            "EPG interpretation",
            "How profiles were interpreted: NoC, statistics, allele frequencies.",
            ((epi, epi.id == pcr.epg_interpretation_method_id),),
        ),
    ]
    return tables, _pcr_fields(pcr, pm, ce, epa, epi, post)


def _pcr_fields(pcr, pm, ce, epa, epi, post) -> list[Field]:
    g = "PCR"
    pg = "PCR method"
    cg = "CE method"
    ag = "EPG analysis"
    ig = "EPG interpretation"
    return [
        Field("pcr.id", "PCR ID", g, "string", cast(pcr.id, String)),
        Field("pcr.sample_input_volume", "Sample input volume", g, "number", pcr.sample_input_volume_in_pcr, unit="µl"),
        Field("pcr.dna_input_amount", "DNA input amount", g, "number", pcr.dna_input_amount_in_pcr, unit="ng"),
        Field("pcr.no_of_contributors", "Number of contributors", g, "number", pcr.no_of_contributors),
        Field("pcr.total_rfu", "Total RFU", g, "number", pcr.total_rfu),
        Field("pcr.total_no_of_alleles", "Total number of alleles", g, "number", pcr.total_no_of_alleles),
        Field("pcr_method.id", "PCR method ID", pg, "string", cast(pm.id, String)),
        Field("pcr_method.kit", "PCR kit", pg, "category", lookup(PCRKit, pm.pcr_kit_id)),
        Field("pcr_method.thermocycler", "Thermocycler", pg, "category", lookup(Thermocycler, pm.thermocycler_id)),
        Field("pcr_method.no_of_cycles", "Number of cycles", pg, "number", pm.no_of_cycles),
        Field("pcr_method.annealing_temp", "Annealing temperature", pg, "number", pm.annealing_temp, unit="°C"),
        Field("pcr_method.total_volume", "Total PCR reaction volume", pg, "number", pm.total_volume_pcr_reaction, unit="µl"),
        Field("post_pcr.purification", "Post-PCR purification", pg, "boolean", post.application_of_post_pcr_purification_step),
        Field("post_pcr.dilution_factor", "Dilution factor of PCR product", pg, "number", post.dilution_factor),
        Field("ce_method.id", "CE method ID", cg, "string", cast(ce.id, String)),
        Field("ce_method.device", "CE device", cg, "category", lookup(CEDevice, ce.ce_device_id)),
        Field("ce_method.polymer", "Polymer", cg, "category", lookup(Polymer, ce.polymer_id)),
        Field("ce_method.dye_set", "Dye set", cg, "category", lookup(DyeSet, ce.dye_set_id)),
        Field("ce_method.size_standard", "Size standard", cg, "category", lookup(SizeStandard, ce.size_standard_id)),
        Field("ce_method.injection_voltage", "Injection voltage", cg, "number", ce.injection_voltage, unit="kV"),
        Field("ce_method.injection_time", "Injection time", cg, "number", seconds(ce.injection_time), unit="s"),
        Field("epg_analysis.id", "EPG analysis method ID", ag, "string", cast(epa.id, String)),
        Field("epg_analysis.software", "Genotyping software", ag, "category", lookup(GenotypingSoftware, epa.genotyping_software_id)),
        Field("epg_analysis.analytical_threshold", "Analytical threshold", ag, "string", epa.application_analytical_threshold),
        Field("epg_analysis.stutter_filter", "Stutter filter", ag, "category", lookup(StutterFilter, epa.stutter_filter_id)),
        Field("epg_interpretation.id", "EPG interpretation method ID", ig, "string", cast(epi.id, String)),
        Field("epg_interpretation.determination_of_noc", "Determination of NoC", ig, "string", epi.determination_of_noc),
        Field(
            "epg_interpretation.statistical_software",
            "Statistical software",
            ig,
            "category",
            lookup(StatisticalSoftware, epi.statistical_software_id),
        ),
        Field("epg_interpretation.allele_frequency_database", "Allele frequency database", ig, "string", epi.allele_frequency_database),
        Field(
            "epg_interpretation.analytical_threshold",
            "Interpretation threshold",
            ig,
            "category",
            lookup(ApplicationAnalyticalThreshold, epi.application_analytical_threshold_id),
        ),
    ]


# --- Datasets ---------------------------------------------------------------


def _results_dataset() -> Dataset:
    res = aliased(Result)
    sm = aliased(Sample)
    ctx = _sample_context(join(res, sm, sm.id == res.sample_id), sm)
    result_tables, result_fields = _result_tables(res)
    return Dataset(
        key="results",
        label="Results",
        description="One row per quantification result.",
        base=ctx.base,
        tables=[
            table("Result", "The quantification result: DNA concentration, degradation, inhibition.", required=True),
            *ctx.tables,
            *result_tables,
        ],
        study_id=ctx.study.id,
        row_id=res.id,
        default_sort=["study.title", "sample.name"],
        fields=[*ctx.fields, *result_fields],
    )


def _pcr_dataset() -> Dataset:
    pcr = aliased(PCR)
    res = aliased(Result)
    sm = aliased(Sample)
    from_ = join(pcr, res, res.id == pcr.result_id).join(sm, sm.id == res.sample_id)
    ctx = _sample_context(from_, sm)
    result_tables, result_fields = _result_tables(res)
    pcr_tables, pcr_fields = _pcr_tables(pcr)
    return Dataset(
        key="pcr_profiles",
        label="PCR profiles",
        description="One row per PCR (STR profile).",
        base=ctx.base,
        tables=[
            table("PCR", "The PCR and its profile summary: contributors, RFU, alleles.", required=True),
            table("Result", "The quantification result the PCR was run on.", required=True),
            *ctx.tables,
            *result_tables,
            *pcr_tables,
        ],
        study_id=ctx.study.id,
        row_id=pcr.id,
        default_sort=["study.title", "sample.name"],
        fields=[*ctx.fields, *result_fields, *pcr_fields],
    )


def _contributors_dataset() -> Dataset:
    con = aliased(PCRContributor)
    pcr = aliased(PCR)
    res = aliased(Result)
    sm = aliased(Sample)
    ind = aliased(Individual)
    from_ = (
        join(con, pcr, pcr.id == con.pcr_id)
        .join(res, res.id == pcr.result_id)
        .join(sm, sm.id == res.sample_id)
        .outerjoin(ind, ind.id == con.individual_id)
    )
    ctx = _sample_context(from_, sm)
    result_tables, result_fields = _result_tables(res)
    pcr_tables, pcr_fields = _pcr_tables(pcr)
    g = "Contributor"
    contributor_fields = [
        Field(
            "contributor.label",
            "Contributor",
            g,
            "category",
            func.coalesce(ind.name, con.unknown_label),
            description="The known individual, or the label of an unknown person (e.g. UP1).",
        ),
        Field("contributor.known", "Known individual", g, "boolean", con.individual_id.is_not(None)),
        Field("contributor.mixture_proportion", "Mixture proportion", g, "number", con.mixture_proportion),
        *[f for f in individual_fields(ind, "contributor.individual", g) if f.key != "contributor.individual.name"],
    ]
    return Dataset(
        key="pcr_contributors",
        label="Mixture contributors",
        description="One row per contributor to a PCR profile.",
        base=ctx.base,
        tables=[
            table(
                "Contributor",
                "Who contributed to the profile and how much, with the contributor's sex, age and shedder status.",
                required=True,
            ),
            table("PCR", "The PCR profile the contributor was found in.", required=True),
            table("Result", "The quantification result the PCR was run on.", required=True),
            *ctx.tables,
            *result_tables,
            *pcr_tables,
        ],
        study_id=ctx.study.id,
        row_id=con.id,
        default_sort=["study.title", "sample.name", "contributor.label"],
        fields=[*ctx.fields, *result_fields, *pcr_fields, *contributor_fields],
    )


def _surface_study(surface_id) -> ColumnElement:
    """The study of the individual a surface belongs to, if any."""
    su = aliased(Surface)
    ind = aliased(Individual)
    return (
        select(ind.study_id)
        .select_from(su)
        .join(ind, ind.id == su.individual_id)
        .where(su.id == surface_id)
        .scalar_subquery()
    )


def _contacts_dataset() -> Dataset:
    co = aliased(Contact)
    cot = aliased(ContactTemplate)
    st = aliased(Study)
    lab = aliased(Laboratory)

    # A contact belongs to the study of its individuals, else the study of
    # the samples taken after it, else the owning study of its scenario.
    # Subqueries rather than joins, so the surfaces stay optional tables.
    sample_alias = aliased(Sample)
    sample_study = (
        select(sample_alias.study_id)
        .where(sample_alias.contact_id == co.id)
        .limit(1)
        .scalar_subquery()
    )
    sc = aliased(Scenario)
    scenario_study = (
        select(sc.owning_study_id)
        .join(scenario_contact_template, scenario_contact_template.c.scenario_id == sc.id)
        .where(scenario_contact_template.c.contact_template_id == co.contact_template_id)
        .order_by(sc.owning_study_id)
        .limit(1)
        .scalar_subquery()
    )
    study_id = func.coalesce(
        _surface_study(co.donor_surface_id),
        _surface_study(co.recipient_surface_id),
        sample_study,
        scenario_study,
    )
    base = outerjoin(co, cot, cot.id == co.contact_template_id).join(st, st.id == study_id)

    donor_table, donor_fields = _surface_table(
        "Donor surface", "The surface DNA was transferred from.", co.donor_surface_id, "donor_surface"
    )
    recipient_table, recipient_fields = _surface_table(
        "Recipient surface", "The surface DNA was transferred to.", co.recipient_surface_id, "recipient_surface"
    )
    samples_taken = (
        select(func.count(sample_alias.id)).where(sample_alias.contact_id == co.id).scalar_subquery()
    )
    return Dataset(
        key="contacts",
        label="Contacts",
        description="One row per contact performed.",
        base=base,
        tables=[
            table("Contact", "The contact: duration, pressure, friction, activity.", required=True),
            table("Study", "The study the contact belongs to.", required=True),
            table("Laboratory", "The laboratory that conducted the study.", ((lab, lab.id == st.laboratory_id),)),
            table("Conditions during contact", "Temperature, humidity and location during the contact."),
            table("Scenario", "The scenario of the contact, within the row's study."),
            table("Persistence", "Persistence settings of the scenario (time, temperature, humidity, …)."),
            donor_table,
            recipient_table,
        ],
        study_id=st.id,
        row_id=co.id,
        default_sort=["study.title", "contact.name"],
        fields=[
            *study_fields(st, lab),
            *scenario_fields(cot.id, st.id),
            *contact_fields(co, cot),
            Field("contact.samples_taken", "Samples taken", "Contact", "number", samples_taken),
            *donor_fields,
            *recipient_fields,
        ],
    )


def _individuals_dataset() -> Dataset:
    ind = aliased(Individual)
    st = aliased(Study)
    lab = aliased(Laboratory)
    sc = aliased(Scenario)
    scenarios = (
        select(string_agg(sc.name))
        .select_from(individual_scenario)
        .join(sc, sc.id == individual_scenario.c.scenario_id)
        .where(individual_scenario.c.individual_id == ind.id)
        .scalar_subquery()
    )
    return Dataset(
        key="individuals",
        label="Individuals",
        description="One row per study participant.",
        base=join(ind, st, st.id == ind.study_id),
        tables=[
            table("Individual", "The participant: sex, age, shedder status, skin conditions.", required=True),
            table("Study", "The study the participant took part in.", required=True),
            table("Laboratory", "The laboratory that conducted the study.", ((lab, lab.id == st.laboratory_id),)),
        ],
        study_id=st.id,
        row_id=ind.id,
        default_sort=["study.title", "individual.name"],
        fields=[
            *study_fields(st, lab),
            *individual_fields(ind, "individual", "Individual"),
            Field("individual.scenarios", "Scenarios", "Individual", "string", scenarios),
        ],
    )


def _studies_dataset() -> Dataset:
    st = aliased(Study)
    lab = aliased(Laboratory)
    sm = aliased(Sample)
    res = aliased(Result)
    ind = aliased(Individual)
    sc = aliased(Scenario)
    g = "Counts"
    counts = [
        Field(
            "study.scenarios",
            "Scenarios",
            "Study",
            "string",
            select(string_agg(sc.name))
            .select_from(study_scenario)
            .join(sc, sc.id == study_scenario.c.scenario_id)
            .where(study_scenario.c.study_id == st.id)
            .scalar_subquery(),
        ),
        Field(
            "count.samples",
            "Number of samples",
            g,
            "number",
            select(func.count(sm.id)).where(sm.study_id == st.id).scalar_subquery(),
        ),
        Field(
            "count.results",
            "Number of results",
            g,
            "number",
            select(func.count(res.id))
            .join(sm, sm.id == res.sample_id)
            .where(sm.study_id == st.id)
            .scalar_subquery(),
        ),
        Field(
            "count.individuals",
            "Number of individuals",
            g,
            "number",
            select(func.count(ind.id)).where(ind.study_id == st.id).scalar_subquery(),
        ),
    ]
    return Dataset(
        key="studies",
        label="Studies",
        description="One row per study.",
        base=st,
        tables=[
            table("Study", "Bibliographic data: title, authors, year, journal, DOI.", required=True),
            table("Laboratory", "The laboratory that conducted the study.", ((lab, lab.id == st.laboratory_id),)),
            table("Counts", "How much data each study holds."),
        ],
        study_id=st.id,
        row_id=st.id,
        default_sort=["study.year", "study.title"],
        fields=[
            *study_fields(st, lab),
            Field("study.abstract", "Abstract", "Study", "string", st.abstract),
            *counts,
        ],
    )


_BUILDERS: list[Callable[[], Dataset]] = [
    _results_dataset,
    _pcr_dataset,
    _contributors_dataset,
    _contacts_dataset,
    _individuals_dataset,
    _studies_dataset,
]

DATASETS: dict[str, Dataset] = {ds.key: ds for ds in (build() for build in _BUILDERS)}


def get_dataset(key: str) -> Optional[Dataset]:
    return DATASETS.get(key)
