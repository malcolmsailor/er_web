Get following from ERSettings:
- field name
- default value
- expected type(s)
- other validation stuff (min/max values, allowed values, etc.) -> use metadata for this
- TODO later: possibly other data like
    - description
    - priority
    - category ("rhythm", "chords", etc.)

Create a validator function that
- takes a string
- parses it (i.e., with ast.literal_eval) (eventually, I should perhaps allow a simpler syntax for lists and the like)
- type-checks it
- checks it against min/max values if applicable

dataclass fields should have:
- type annotation
- default value OR default_factory
- metadata dict containing
    - priority level
    - category
    - description
    - validation functions and args

regex for matching fields
^(    \w+:.+? = )([\w\."]+)

# LONGTERM:

allow upload of midi files for "existing voices" and "rhythms in midi" etc.



# TODO
- num reps super pattern = 1 bug
- download settings as Python dict (to be used with CLI)
- document validation constraints
- randomize button
- list presets (eventually buttons to add)
- default settings fail when attack_density = 1.0

# CSS

- tooltips should remain in view
