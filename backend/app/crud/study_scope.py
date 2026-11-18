"""Which records belong to a study, as SQL conditions for list endpoints.

These mirror how the data entry page scopes its tabs, so filtering on the
server returns the same rows the page used to pick out of full table dumps:
contacts belong to a study through the contact templates of its scenarios
(or the study's individuals they involve), samples through the surfaces of
those contacts (or their own study_id), and results through their sample.
"""

from uuid import UUID

from sqlalchemy import or_, select

from app.models.contact import Contact
from app.models.contact_template import scenario_contact_template
from app.models.individual import Individual
from app.models.sample import Sample
from app.models.scenario import study_scenario
from app.models.surface import Surface


def scenario_ids_of_study(study_id: UUID):
    return select(study_scenario.c.scenario_id).where(
        study_scenario.c.study_id == study_id
    )


def contact_template_ids_of_study(study_id: UUID):
    return select(scenario_contact_template.c.contact_template_id).where(
        scenario_contact_template.c.scenario_id.in_(scenario_ids_of_study(study_id))
    )


def _individual_surface_ids_of_study(study_id: UUID):
    return (
        select(Surface.id)
        .join(Individual, Surface.individual_id == Individual.id)
        .where(Individual.study_id == study_id)
    )


def contact_in_study(study_id: UUID):
    individual_surfaces = _individual_surface_ids_of_study(study_id)
    return or_(
        Contact.contact_template_id.in_(contact_template_ids_of_study(study_id)),
        Contact.donor_surface_id.in_(individual_surfaces),
        Contact.recipient_surface_id.in_(individual_surfaces),
    )


def _contact_surface_ids_of_study(study_id: UUID):
    templates = contact_template_ids_of_study(study_id)
    return select(Contact.donor_surface_id).where(
        Contact.contact_template_id.in_(templates)
    ).union(
        select(Contact.recipient_surface_id).where(
            Contact.contact_template_id.in_(templates)
        )
    )


def sample_in_study(study_id: UUID):
    return or_(
        Sample.study_id == study_id,
        Sample.surface_id.in_(_contact_surface_ids_of_study(study_id)),
    )


def sample_ids_of_study(study_id: UUID):
    return select(Sample.id).where(sample_in_study(study_id))
