import pytest
from update.utils import (
    Periodo,
    periodoMasReciente,
    periodoValido,
    normalize_text,
)

# Periodos


@pytest.fixture
def invalid_periodos():
    return [
        "OTOÑO 2023",
        "OTOÑO 2023 POSGRADO",
        "FALL 2023 LICENCIATURA",
        "OTOÑO XXX LICENCIATURA",
    ]


@pytest.fixture
def valid_periodos():
    return [
        "OTOÑO 2023 LICENCIATURA",
        "PRIMAVERA 2022 LICENCIATURA",
        "VERANO 2021 LICENCIATURA",
        "OTOÑO 2022 LICENCIATURA",
    ]


@pytest.fixture
def sorted_periodos():  # descending order
    return [
        "PRIMAVERA 2011 LICENCIATURA",
        "OTOÑO 2010 LICENCIATURA",
        "VERANO 2010 LICENCIATURA",
        "PRIMAVERA 2010 LICENCIATURA",
        "OTOÑO 2000 LICENCIATURA",
    ]


def test_valid_periodo_init(valid_periodos):
    for periodo_str in valid_periodos:
        p = Periodo(periodo_str)
        assert p.sem == periodo_str.split()[0]
        assert p.yr == int(periodo_str.split()[1])
        assert p.lic == periodo_str.split()[2]
        assert p.periodo_str == periodo_str.upper()


def test_invalid_periodo_init(invalid_periodos):
    for periodo_str in invalid_periodos:
        with pytest.raises(AssertionError):
            Periodo(periodo_str)


def test_periodo_valido(valid_periodos, invalid_periodos):
    for periodo_str in valid_periodos:
        assert periodoValido(periodo_str) is True

    for periodo_str in invalid_periodos:
        assert periodoValido(periodo_str) is False


def test_sorted_periodos(sorted_periodos):
    periodos = sorted(sorted_periodos, key=lambda p: Periodo(p), reverse=True)
    assert periodos == sorted_periodos


def test_periodo_mas_reciente(sorted_periodos):
    recent_periodo = periodoMasReciente(sorted_periodos)
    assert recent_periodo == sorted_periodos[0]


# Other


def test_normalize_text():
    assert normalize_text("Juan Pérez") == "juan perez"
    assert normalize_text("Cálculo I") == "calculo i"
    assert normalize_text("Foo Bar") == "foo bar"
    assert normalize_text("  Muchos   Espacios  ") == "muchos espacios"
    assert normalize_text("Con-Guiones_y_otros-simbolos") == "conguionesyotrossimbolos"
    assert normalize_text(123) == ""
