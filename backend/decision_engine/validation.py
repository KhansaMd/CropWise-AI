
import re


def validate_explanation(text, result):
    """Reject numeric claims not supported by computed results."""

    allowed_numbers = set()

    score = result.get("overall")
    if score is not None:
        allowed_numbers.add(str(score))
        allowed_numbers.add(f"{score:.2f}")

    for key in ("scores",):
        for value in result.get(key, {}).values():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                allowed_numbers.add(str(value))

    for item in result.get("climate_risks", []):
        value = item.get("observed_value")
        if isinstance(value, (int, float)):
            allowed_numbers.add(str(value))

    found_numbers = re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?", text)

    for number in found_numbers:
        if number not in allowed_numbers:
            return False

    return True
