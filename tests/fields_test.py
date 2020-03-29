import datetime

import pytest

from api import CharField, ArgumentsField, EmailField, PhoneField, DateField, BirthDayField, GenderField, ClientIDsField


@pytest.mark.parametrize("value, required, nullable", (
        ("123", False, False),
        ("qwe", False, False),
        ("", False, False),
        ("", True, False),
        ("", False, True),
        ("", True, True),
        (None, True, True),
))
def test_success_char_field(value, required, nullable):
    charField = CharField(required, nullable)
    CharField.__set__(charField, charField, value)
    assert CharField.__get__(charField, charField, 'data') == value


@pytest.mark.parametrize("value, required, nullable", (
        (None, False, False),
        (111, False, False),
        ([], False, False),
        (None, True, False),
))
def test_false_char_field(value, required, nullable):
    charField = CharField(required, nullable)
    with pytest.raises(ValueError):
        CharField.__set__(charField, charField, value)


@pytest.mark.parametrize("value, required, nullable", (
        ({}, False, False),
        ({"1": 1}, False, False),
))
def test_success_argument_field(value, required, nullable):
    argument_filed = ArgumentsField(required, nullable)
    ArgumentsField.__set__(argument_filed, argument_filed, value)
    assert ArgumentsField.__get__(argument_filed, argument_filed, 'data') == value


@pytest.mark.parametrize("value, required, nullable", (
        ([], False, False),
        (None, True, False),
        ("None", True, False),
        (123, True, False),
))
def test_false_argument_field(value, required, nullable):
    argument_filed = ArgumentsField(required, nullable)
    with pytest.raises(ValueError):
        ArgumentsField.__set__(argument_filed, argument_filed, value)


@pytest.mark.parametrize("value, required, nullable", (
        ("@", False, False),
        ("a@a", False, False),
        ("@@", False, False),
        ("1/@/@", False, False),
        ("admin@localhost.com", False, False),
        (None, False, True),
))
def test_success_email_field(value, required, nullable):
    email_filed = EmailField(required, nullable)
    EmailField.__set__(email_filed, email_filed, value)
    assert EmailField.__get__(email_filed, email_filed, 'data') == value


@pytest.mark.parametrize("value, required, nullable, message", (
        ([], False, False, "EmailField must be string!"),
        (None, True, False, "EmailField must be string!"),
        ("None", True, False, "Email must be contain '@'"),
        (123, True, False, "EmailField must be string!"),
        ({"@": "@"}, True, False, "EmailField must be string!"),
))
def test_false_email_field(value, required, nullable, message):
    email_filed = EmailField(required, nullable)
    with pytest.raises(ValueError) as e:
        EmailField.__set__(email_filed, email_filed, value)
    assert message in str(e.value)


@pytest.mark.parametrize("value, required, nullable", (
        ('71234567891', False, False),
        (71234567891, False, False),
        (None, False, True),
))
def test_success_phone_field(value, required, nullable):
    phone_filed = PhoneField(required, nullable)
    PhoneField.__set__(phone_filed, phone_filed, value)
    assert PhoneField.__get__(phone_filed, phone_filed, 'data') == (str(value) if value else None)


@pytest.mark.parametrize("value, required, nullable, message", (
        ([], False, False, "Number phone must be str or int"),
        (None, True, False, "Number phone must be str or int"),
        ("None", True, False, "Phone numbers must be contain 11 numbers"),
        (12345678911, True, False, "Phone must be start with 7"),
        (1234567891, True, False, "Phone numbers must be contain 11 numbers"),
))
def test_false_phone_field(value, required, nullable, message):
    phone_filed = PhoneField(required, nullable)
    with pytest.raises(ValueError) as e:
        PhoneField.__set__(phone_filed, phone_filed, value)
    assert message == str(e.value)


@pytest.mark.parametrize("value, required, nullable", (
        ('03.11.2020', False, False),
        (None, False, True),
))
def test_success_date_filed(value, required, nullable):
    date_filed = DateField(required, nullable)
    DateField.__set__(date_filed, date_filed, value)
    assert DateField.__get__(date_filed, date_filed, 'data') == (datetime.datetime.strptime(value, "%d.%m.%Y") if value
                                                                 else None)


@pytest.mark.parametrize("value, required, nullable, message", (
        ([], False, False, "DateField must be string!"),
        (None, True, False, "DateField must be string!"),
        (12345678911, True, False, "DateField must be string!"),
        ("None", True, False, "Date must be date format DD.MM.YYYY !"),
        ("15.15.2020", True, False, "Date must be date format DD.MM.YYYY !"),
))
def test_false_date_filed(value, required, nullable, message):
    date_filed = DateField(required, nullable)
    with pytest.raises(ValueError) as e:
        DateField.__set__(date_filed, date_filed, value)
    assert message == str(e.value)

#    # BirthDayField


@pytest.mark.parametrize("value, required, nullable", (
        ('03.11.2020', False, False),
        (f"{str(datetime.datetime.now().day + 1)}."
         f"{str(datetime.datetime.now().month)}."
         f"{str(datetime.datetime.now().year - 70)}", True, False),
        (None, False, True),
))
def test_success_birth_day_filed(value, required, nullable):
    birth_day_filed = BirthDayField(required, nullable)
    BirthDayField.__set__(birth_day_filed, birth_day_filed, value)
    assert BirthDayField.__get__(birth_day_filed, birth_day_filed, 'data') == (
        datetime.datetime.strptime(value, "%d.%m.%Y") if value else None)


@pytest.mark.parametrize("value, required, nullable, message", (
        ([], False, False, "BirthDayField must be string!"),
        (None, True, False, "BirthDayField must be string!"),
        (12345678911, True, False, "BirthDayField must be string!"),
        ("None", True, False, "Date must be date format DD.MM.YYYY !"),
        ("15.15.2020", True, False, "Date must be date format DD.MM.YYYY !"),
        ("10.10.1890", True, False, "Age must be less than 70 years old"),
        (f"10.10.1890", True, False, "Age must be less than 70 years old"),
        (f"{str(datetime.datetime.now().day)}."
         f"{str(datetime.datetime.now().month)}."
         f"{str(datetime.datetime.now().year-70)}", True, False, "Age must be less than 70 years old"),
))
def test_false_birth_day_filed(value, required, nullable, message):
    birth_day_filed = BirthDayField(required, nullable)
    with pytest.raises(ValueError) as e:
        BirthDayField.__set__(birth_day_filed, birth_day_filed, value)
    assert message == str(e.value)


@pytest.mark.parametrize("value, required, nullable", (
        (0, False, False),
        (1, False, False),
        (2, False, False),
        (None, False, True),
))
def test_success_gender_filed(value, required, nullable):
    gender_filed = GenderField(required, nullable)
    GenderField.__set__(gender_filed, gender_filed, value)
    assert GenderField.__get__(gender_filed, gender_filed, 'data') == value


@pytest.mark.parametrize("value, required, nullable, message", (
        ([], False, False, "Gender must be 0,1 or 2"),
        (None, True, False, "Gender must be 0,1 or 2"),
        (4, True, False, "Gender must be 0,1 or 2"),
        (-1, True, False, "Gender must be 0,1 or 2"),
        (2**64, True, False, "Gender must be 0,1 or 2"),
        ("None", True, False, "Gender must be 0,1 or 2"),
        ("15.15.2020", True, False, "Gender must be 0,1 or 2"),
))
def test_false_gender_filed(value, required, nullable, message):
    gender_filed = GenderField(required, nullable)
    with pytest.raises(ValueError) as e:
        GenderField.__set__(gender_filed, gender_filed, value)
    assert message == str(e.value)


@pytest.mark.parametrize("value, required, nullable", (
        ([0], False, False),
        ([1, 3], False, False),
        ([-1], False, False),
))
def test_success_client_ids_filed(value, required, nullable):
    client_ids_filed = ClientIDsField(required, nullable)
    ClientIDsField.__set__(client_ids_filed, client_ids_filed, value)
    assert ClientIDsField.__get__(client_ids_filed, client_ids_filed, 'data') == value


@pytest.mark.parametrize("value, required, nullable, message", (
        ([], False, False, "Client ids must be list<int>!"),
        (["1"], False, False, "Client ids must be list<int>!"),
        (["1", "2"], False, False, "Client ids must be list<int>!"),
        ([1, "2"], False, False, "Client ids must be list<int>!"),
        (None, True, False, "Client ids must be list<int>!"),
        (4, True, False, "Client ids must be list<int>!"),
        ("None", True, False, "Client ids must be list<int>!"),
        (None, False, True, "Client ids must be list<int>!"),

))
def test_false_client_ids_filed(value, required, nullable, message):
    client_ids_filed = ClientIDsField(required, nullable)
    with pytest.raises(ValueError) as e:
        ClientIDsField.__set__(client_ids_filed, client_ids_filed, value)
    assert message == str(e.value)
