import inspect

import pssapi.services as services


def test_api_service_methods_have_docstrings():
    for service_name in services.__all__:
        service = getattr(services, service_name)

        for method_name, method in service.__dict__.items():
            if method_name.startswith("_") or not inspect.isfunction(method):
                continue
            assert inspect.getdoc(method), f"{service_name}.{method_name} is missing a docstring"
