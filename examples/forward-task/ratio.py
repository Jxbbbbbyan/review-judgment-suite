def normalise(values):
    """Scale a non-empty sequence by its largest value."""
    maximum = max(values)
    return [value / maximum for value in values]
