import typing as t

import pytest

from aiomanager import NOTHING, Err, Nothing, Ok, Option, Some
from aiomanager.results import IsNothingError, IsNotNothingError, OptionType


def test_isinstance_option_type() -> None:
    assert isinstance(Some(), OptionType)
    assert isinstance(Nothing(), OptionType)
    assert not isinstance(1, OptionType)
    assert not isinstance(tuple, OptionType)


class TestSome:
    def test_default_factory(self) -> None:
        assert Some().is_some() is True
        assert Some().is_nothing() is False
        assert Some()._value is True

    @pytest.mark.parametrize("value", [..., None, 1, "", []])
    def test_factory(self, value: t.Any) -> None:
        assert Some(value).is_some() is True
        assert Some(value).is_nothing() is False
        assert Some(value)._value == value


class TestNothing:
    def test_nothing_factory(self) -> None:
        nothing = Nothing()
        assert nothing.is_nothing()
        assert not nothing.is_some()
        with pytest.raises(AttributeError):
            Nothing()._value  # type: ignore[attr-defined]
        with pytest.raises(IsNothingError):
            Nothing().value

    def test_nothing_singleton(self) -> None:
        assert Nothing() is Nothing()
        assert Nothing() is NOTHING


class TestOptionDunderMethods:
    def test_eq(self) -> None:
        assert Nothing() == Nothing()
        assert Nothing() == NOTHING
        assert Nothing() != Some()
        assert Some(1) == Some(1)
        assert Some(1) != 1
        assert Some(1) != Some(2)
        assert Some(1) != Nothing()
        assert Some(1) != NOTHING

    def test_hash(self) -> None:
        """Hash are used to compare entries within set."""
        assert len({Some(1), Nothing(), Some(1), Nothing()}) == 2
        assert len({Some(1), Some(2)}) == 2
        assert len({Some("a"), NOTHING}) == 2

    def test_bool(self) -> None:
        assert bool(Some()) is True
        assert bool(Nothing()) is False

    def test_iter(self) -> None:
        o = Some(1)
        for _ in range(2):
            assert list(o) == [1]
        assert list(Nothing()) == []

    def test_next(self) -> None:
        o = Some(1)
        assert next(o) == 1
        with pytest.raises(StopIteration):
            assert next(o) == 1
        with pytest.raises(StopIteration):
            next(Nothing())

    @pytest.mark.parametrize("value", [..., None, 1, "", []])
    def test_some_repr(self, value: t.Any) -> None:
        assert repr(Some(value)) == f"Some({repr(value)})"
        assert Some(value) == eval(repr(Some(value)))

    def test_nothing_repr(self) -> None:
        assert repr(Nothing()) == "Nothing()"
        assert Nothing() == eval(repr(Nothing()))


class TestOptionPublicMethods:
    def test_is_some_and(self) -> None:
        assert Some(1).is_some_and(lambda x: x == 1) is True
        assert Some().is_some_and(lambda x: x == 2) is False
        assert Nothing().is_some_and(lambda _: True) is False

    def test_expect(self) -> None:
        assert Some(1).expect("should not fail") == 1
        assert Some(None).expect("should not fail") is None
        assert Some("").expect("should not fail") == ""
        assert Some().expect("should not fail") is True
        with pytest.raises(IsNothingError, match="BOOM") as exc_info:
            Nothing().expect("BOOM")
        assert exc_info.value.option is Nothing()

    def test_expect_empty(self) -> None:
        Nothing().expect_nothing("should not fail")
        with pytest.raises(IsNotNothingError, match="BOOM") as exc_info:
            Some(1).expect_nothing("BOOM")
        assert exc_info.value.option == Some(1)
        with pytest.raises(IsNotNothingError, match="BOOM") as exc_info:
            Some(None).expect_nothing("BOOM")
        assert exc_info.value.option == Some(None)
        with pytest.raises(IsNotNothingError, match="BOOM") as exc_info:
            Some("").expect_nothing("BOOM")
        assert exc_info.value.option == Some("")
        with pytest.raises(IsNotNothingError, match="BOOM") as exc_info:
            Some().expect_nothing("BOOM")
        assert exc_info.value.option == Some()

    def test_unwrap(self) -> None:
        assert Some().unwrap() is True
        assert Some(None).unwrap() is None
        assert Some("").unwrap() == ""
        assert Some(1).unwrap() == 1
        with pytest.raises(IsNothingError):
            Nothing().unwrap()

    def test_unwrap_or(self) -> None:
        assert Some().unwrap_or(False) is True
        assert Some(False).unwrap_or(True) is False
        assert Nothing().unwrap_or(False) is False
        assert Nothing().unwrap_or(True) is True

    def test_unwrap_or_else(self) -> None:
        assert Some().unwrap_or_else(lambda: False) is True
        assert Some(False).unwrap_or_else(lambda: True) is False
        assert Nothing().unwrap_or_else(lambda: False) is False
        assert Nothing().unwrap_or_else(lambda: True) is True

    def test_map(self) -> None:
        assert Some().map(lambda x: x) == Some()
        assert Some(1).map(lambda x: x + 1) == Some(2)
        assert Nothing().map(lambda x: True) is Nothing()

    def test_inspect(self) -> None:
        class Spy:
            def __init__(self) -> None:
                self.provided_arg: Option[int] = Nothing()

            def __call__(self, value: int) -> None:
                self.provided_arg = Some(value)

        spy = Spy()
        Some(1).inspect(spy)
        assert spy.provided_arg == Some(1)

        spy = Spy()
        Nothing().inspect(spy)
        assert spy.provided_arg is Nothing()

    def test_map_or(self) -> None:
        assert Some().map_or(True, lambda b: not b) is False
        assert Nothing().map_or(True, lambda _: False) is True

    def test_map_or_else(self) -> None:
        assert Some().map_or_else(lambda: True, lambda b: not b) is False
        assert Nothing().map_or_else(lambda: True, lambda _: False) is True

    def test_ok_or(self) -> None:
        assert Some().ok_or("BOOM") == Ok()
        assert Nothing().ok_or("BOOM") == Err("BOOM")

    def test_ok_or_else(self) -> None:
        assert Some().ok_or_else(lambda: "BOOM") == Ok()
        assert Nothing().ok_or_else(lambda: "BOOM") == Err("BOOM")

    def test_and_option(self) -> None:
        assert Some().and_option(Nothing()) is Nothing()
        assert Nothing().and_option(Some()) is Nothing()
        assert Some().and_option(Some()) == Some()
        assert Some().and_option(Some(False)) == Some(False)

    def test_and_then(self) -> None:
        assert Some().and_then(lambda v: Some(not v)) == Some(False)
        assert Some().and_then(lambda v: Some(v)) == Some()
        assert Nothing().and_then(lambda _: Some()) is Nothing()

    def test_filter(self) -> None:
        assert Some().filter(lambda v: v) == Some()
        assert Some().filter(lambda v: not v) is Nothing()
        assert Nothing().filter(lambda _: True) is Nothing()

    def test_or_option(self) -> None:
        assert Some().or_option(Nothing()) == Some()
        assert Some().or_option(Some(2)) == Some()
        assert Nothing().or_option(Some(2)) == Some(2)
        assert Nothing().or_option(Nothing()) is Nothing()

    def test_or_else(self) -> None:
        assert Some().or_else(lambda: Nothing()) == Some()
        assert Some().or_else(lambda: Some(2)) == Some()
        assert Nothing().or_else(lambda: Some(2)) == Some(2)
        assert Nothing().or_else(lambda: Nothing()) is Nothing()

    def test_xor(self) -> None:
        assert Some().xor(Some()) is Nothing()
        assert Nothing().xor(Nothing()) is Nothing()
        assert Some().xor(Nothing()) == Some()
        assert Nothing().xor(Some()) == Some()

    @pytest.mark.parametrize("value", [..., None, 1, "", []])
    def test_contains(self, value: t.Any) -> None:
        assert Some(value).contains(value) is True
        assert Some("something else").contains(value) is False
        assert Nothing().contains(value) is False

    def test_zip(self) -> None:
        assert Some().zip(Some(2)) == Some((True, 2))
        assert Some().zip(Nothing()) is Nothing()
        assert Nothing().zip(Nothing()) is Nothing()
        assert Nothing().zip(Some()) is Nothing()

    def test_zip_with(self) -> None:
        assert Some().zip_with(
            Some(2), lambda flag, value: value if flag else 0
        ) == Some(2)
        assert Some(False).zip_with(
            Some(2), lambda flag, value: value if flag else 0
        ) == Some(0)
        assert Some().zip_with(Nothing(), lambda _, __: True) is Nothing()  # type: ignore[misc]
        assert Nothing().zip_with(Nothing(), lambda _, __: True) is Nothing()
        assert Nothing().zip_with(Some(), lambda _, __: True) is Nothing()
