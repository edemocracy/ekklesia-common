from {{ cookiecutter.app_package }}.datamodel import {{ cookiecutter.ConceptName }}


class {{ cookiecutter.ConceptNames }}:

    def {{ cookiecutter.concept_names }}(self, q):
        query = q({{ cookiecutter.ConceptName }})
        return query.all()
