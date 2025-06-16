import pint

# defines the application-wide unit registry
ureg = pint.UnitRegistry()
pint.set_application_registry(ureg)


def force_units(v, type_):
    return (
        v.to(type_) if isinstance(v, ureg.Quantity) else ureg.Quantity(v, type_)
    )
