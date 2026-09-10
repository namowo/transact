# Roadmap

This document gives an overview of the current development status of TransAct and the next planned steps. It is updated alongside ongoing development.

## Current status

The project is in an early build-up phase. Implemented so far:

- [x] **Data model**: Extensive domain-specific data model for forensic transfer experiments (e.g. items, contacts, individuals, laboratories, extraction/PCR/CE methods, classification schemes, shedding propensity categories).
- [x] **Backend API**: FastAPI routers, CRUD, and schema layer for the entities above, plus Alembic migrations.
- [x] **Auth**: JWT-based login (HttpOnly cookie) and WebAuthn/passkey support; admin user setup.
- [x] **Lab and study management**: Laboratories, membership requests, studies including ownership ("owning study").
- [x] **Frontend**: Initial dashboard, settings area (scenarios, methods, reference data), and input forms built with Vue 3 / PrimeVue.
- [x] **Initial data**: Scripts for seeding reference data (`initial_data.py`, init data files).

## Next steps

- [ ] Finalize the input forms for all reference-data categories.
- [ ] Refine the UI/UX of the frontend.
- [ ] Extensive testing phase (backend and frontend).
- [ ] Implement data export and import.

## Note

This status is a snapshot in time. For the actual code and feature state, `git log` and the current [backend/app/](../backend/app/) and [frontend/src/](../frontend/src/) directories are authoritative.
