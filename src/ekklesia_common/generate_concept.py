"""
Generate a basic CRU (Delete is not implemented) concept that provides views for a database model object.

The script must be run from the project's root dir, for example:

    python ../ekklesia-common/cookiecutter/concept/generate.py my_concept
"""
import sys
from pathlib import Path

import case_conversion
import inflection
from cookiecutter.main import cookiecutter as run_cookiecutter
from pkg_resources import resource_filename

COOKIECUTTER_TEMPLATE = resource_filename("ekklesia_common", "cookiecutter/concept")


def main():
    if len(sys.argv) == 1:
        raise Exception("expected one argument: concept name is missing!")

    candidate_app_packages = [
        p for p in Path.cwd().glob("src/ekklesia_*") if "." not in p.name
    ]
    if not candidate_app_packages:
        raise Exception(
            "app package in src cannot be found. Did you run the script from the root "
            "directory of a ekklesia project?"
        )
    if len(candidate_app_packages) > 1:
        raise Exception("Multiple candidates for the app package in src!")

    app_package = candidate_app_packages[0]
    concepts_package = app_package / "concepts"
    concept_name = sys.argv[1]

    concept_name_plural = inflection.pluralize(concept_name)
    concept_name_camelcase_upper = case_conversion.pascalcase(concept_name)
    concept_name_camelcase_upper_plural = case_conversion.pascalcase(
        concept_name_plural
    )

    extra_context = {
        "app_package": app_package.name,
        "concept_name": concept_name,
        "concept_names": concept_name_plural,
        "ConceptName": concept_name_camelcase_upper,
        "ConceptNames": concept_name_camelcase_upper_plural,
    }

    run_cookiecutter(
        COOKIECUTTER_TEMPLATE,
        output_dir=concepts_package,
        no_input=True,
        extra_context=extra_context,
    )

    print(
        f"generated concept {concepts_package / concept_name}, tests are located at "
        f"tests/concepts/{concept_name}"
    )


if __name__ == "__main__":
    main()
