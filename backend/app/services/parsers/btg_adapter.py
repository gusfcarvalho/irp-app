from app.models.schemas import Trade


class BTGParserAdapter:
    """Adapter placeholder to normalize CorrePy brokerage note output."""

    def parse(self, pdf_path: str) -> list[Trade]:
        # TODO: integrate CorrePy parser for BTG notes.
        # Expected return: list[Trade] normalized by domain schema.
        return []
