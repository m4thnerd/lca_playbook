from __future__ import annotations

from dataclasses import dataclass


_HEADER_VARIANTS = ("# Essential Requirements", "## Essential Requirements")


@dataclass(frozen=True)
class EssentialRequirementsValidation:
    ok: bool
    message: str


def validate_essential_requirements(content: str) -> EssentialRequirementsValidation:
    """Validate the design doc's required Essential Requirements section.

    Accepts either `# Essential Requirements` or `## Essential Requirements` as
    the section header. Allows blank line(s) between the header and the first
    bullet. Allows requirements written in a word-wrap style where lines that
    don't start with `- ` continue the previous bullet. The section ends at
    the first blank line after content (or at the next heading / EOF).
    """
    lines = content.splitlines()
    section_start = None
    for i, line in enumerate(lines):
        if line.strip() in _HEADER_VARIANTS:
            section_start = i
            break

    if section_start is None:
        return EssentialRequirementsValidation(
            ok=False,
            message=(
                'Design doc missing required "# Essential Requirements" section.\n'
                '       Add a section starting with "# Essential Requirements" (or\n'
                '       "## Essential Requirements") followed by a bullet-point list\n'
                "       (1-10 items) of the essential requirements."
            ),
        )

    requirement_count = 0
    have_open_requirement = False
    seen_content = False

    for i in range(section_start + 1, len(lines)):
        line = lines[i]
        stripped = line.strip()

        if line.startswith("#"):
            break

        if not stripped:
            if not seen_content:
                # Allow blank line(s) between header and first bullet.
                continue
            # Blank line after content marks the end of the section.
            break

        if line.startswith("- "):
            requirement_count += 1
            have_open_requirement = True
            seen_content = True
            continue

        if not have_open_requirement and stripped.startswith("ER Sign-Off Status:"):
            continue

        if not have_open_requirement:
            return EssentialRequirementsValidation(
                ok=False,
                message=(
                    "Essential Requirements section contains non-bullet-point content\n"
                    f'       on line {i + 1}: "{stripped}"\n'
                    '       Each requirement must start with "- ".'
                ),
            )
        # Otherwise this is a continuation line for the current requirement.

    if requirement_count == 0:
        return EssentialRequirementsValidation(
            ok=False,
            message=(
                "Essential Requirements section is empty.\n"
                "       Add 1-10 bullet points listing the essential requirements."
            ),
        )
    if requirement_count > 10:
        return EssentialRequirementsValidation(
            ok=False,
            message=(
                f"Essential Requirements section contains {requirement_count} items (max 10).\n"
                "       Reduce to only the truly essential requirements. A focused scope\n"
                "       anchor is critical for reviewer convergence."
            ),
        )

    return EssentialRequirementsValidation(ok=True, message="essential requirements exist")
