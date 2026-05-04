# Engineering Plan Mapping

This skeleton maps the requested modules:

- Importer: `backend/app/api/upload.py`, `backend/app/services/parsers/btg_adapter.py`
- Domain models: `backend/app/models/schemas.py`
- Position engine: `backend/app/services/position_engine.py`
- Tax engine: `backend/app/services/tax_engine.py`
- Frontend screens: `frontend/src/pages/*`

Next step: implement persistence (SQLite + SQLModel), parser integration, and end-to-end flows.
