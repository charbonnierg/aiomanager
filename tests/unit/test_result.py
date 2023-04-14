from __future__ import annotations

import typing as t
from typing import Callable

import pytest

from aiomanager.results import (
    Err,
    IsNotOkError,
    IsOkError,
    Nothing,
    Ok,
    Option,
    Result,
    ResultType,
    Some,
)


def test_isinstance_result_type() -> None:
    assert isinstance(Ok(), ResultType)
    assert isinstance(Err(), ResultType)
    assert not isinstance(1, ResultType)
    assert not isinstance(tuple, ResultType)


def test_slots() -> None:
    """
    Ok and Err have slots, so assigning arbitrary attributes fails.
    """
    with pytest.raises(AttributeError):
        Ok().some_arbitrary_attribute = 1  # type: ignore[attr-defined]
    with pytest.raises(AttributeError):
        Err().some_arbitrary_attribute = 1  # type: ignore[attr-defined]


class TestOk:
    def test_default_factory(self) -> None:
        assert Ok().is_ok() is True
        assert Ok().is_err() is False
        assert Ok()._value is True

    def test_ok_factory(self) -> None:
        assert Ok(1).is_ok() is True
        assert Ok(1).is_err() is False
        assert Ok(1)._value == 1
        assert Ok(1).value == 1


class TestErr:
    def test_default_factory(self) -> None:
        assert Err().is_err() is True
        assert Err().is_ok() is False
        assert Err()._value is False
        assert Err().value is False

    def test_err_factory(self) -> None:
        assert Err(2).is_err() is True
        assert Err(2).is_ok() is False
        assert Err(2)._value == 2
        assert Err(2).value == 2


class TestResultDunderMethods:
    def test_eq(self) -> None:
        assert Ok(1) == Ok(1)
        assert Err(1) == Err(1)
        assert Ok(1) != Err(1)
        assert Ok(1) != Ok(2)
        assert Err(1) != Err(2)
        assert not (Ok(1) != Ok(1))  # NOSONAR
        assert Ok(1) != "abc"
        assert Ok("0") != Ok(0)

    def test_hash(self) -> None:
        assert len({Ok(1), Err("2"), Ok(1), Err("2")}) == 2
        assert len({Ok(1), Ok(2)}) == 2
        assert len({Ok("a"), Err("a")}) == 2

    @pytest.mark.parametrize("value", [..., None, 1, "", []])
    def test_repr(self, value: t.Any) -> None:
        assert repr(Ok(value)) == f"Ok({repr(value)})"
        assert Ok(value) == eval(repr(Ok(value)))

        assert repr(Err(value)) == f"Err({repr(value)})"
        assert Err(value) == eval(repr(Err(value)))

    def test_iter(self) -> None:
        assert list(Ok(1)) == [1]
        o = Ok(1)
        for _ in range(2):
            assert list(o) == [1]
        assert list(Err(1)) == []
        e = Err(1)
        for _ in range(2):
            assert list(e) == []


class TestResultPublicMethods:
    def test_is_ok(self) -> None:
        assert Ok().is_ok() is True
        assert Err().is_ok() is False

    def test_is_ok_and(self) -> None:
        assert Ok(1).is_ok_and(lambda v: v == 1) is True
        assert Ok(1).is_ok_and(lambda v: v == 2) is False
        assert Err().is_ok_and(lambda _: True) is False

    def test_is_err(self) -> None:
        assert Ok().is_err() is False
        assert Err().is_err() is True

    def test_is_err_and(self) -> None:
        assert Err(1).is_err_and(lambda v: v == 1) is True
        assert Err(1).is_err_and(lambda v: v == 2) is False
        assert Ok().is_err_and(lambda _: True) is False

    def test_ok(self) -> None:
        assert Ok("yay").ok() == Some("yay")
        assert Err("nay").ok() is Nothing()

    def test_err(self) -> None:
        assert Ok("yay").err() is Nothing()
        assert Err("nay").err() == Some("nay")

    def test_map(self) -> None:
        assert Ok("yay").map(str.upper).ok() == Some("YAY")
        assert Err("nay").map(str.upper).ok() is Nothing()

        assert Ok("yay").map(str.upper).err() is Nothing()
        assert Err("nay").map(str.upper).err() == Some("nay")

    def test_map_err(self) -> None:
        assert Ok("yay").map_err(str.upper).ok() == Some("yay")
        assert Err("nay").map_err(str.upper).err() == Some("NAY")

    def test_map_or(self) -> None:
        assert Ok("yay").map_or("hay", str.upper) == "YAY"
        assert Err("nay").map_or("hay", str.upper) == "hay"
        assert Ok(3).map_or("-1", str) == "3"
        assert Err(2).map_or("-1", str) == "-1"

    def test_map_or_else(self) -> None:
        assert Ok("yay").map_or_else(lambda: "hay", str.upper) == "YAY"
        assert Err("nay").map_or_else(lambda: "hay", str.upper) == "hay"

        assert Ok(3).map_or_else(lambda: "-1", str) == "3"
        assert Err(2).map_or_else(lambda: "-1", str) == "-1"

    def test_inspect(self) -> None:
        class Spy:
            def __init__(self) -> None:
                self.provided_arg: Option[int] = Nothing()

            def __call__(self, value: int) -> None:
                self.provided_arg = Some(value)

        spy = Spy()
        Ok(1).inspect(spy)
        assert spy.provided_arg == Some(1)

        spy = Spy()
        Err(1).inspect(spy)
        assert spy.provided_arg is Nothing()

    def test_inspect_err(self) -> None:
        class Spy:
            def __init__(self) -> None:
                self.provided_arg: Option[int] = Nothing()

            def __call__(self, value: int) -> None:
                self.provided_arg = Some(value)

        spy = Spy()
        Ok(1).inspect_err(spy)
        assert spy.provided_arg is Nothing()

        spy = Spy()
        Err(1).inspect_err(spy)
        assert spy.provided_arg == Some(1)

    def test_expect(self) -> None:
        assert Ok("yay").expect("should not fail") == "yay"
        with pytest.raises(IsNotOkError) as exc_info:
            Err("nay").expect("failure")
        assert exc_info.value.result == Err("nay")

    def test_expect_err(self) -> None:
        assert Err("nay").expect_err("hello") == "nay"
        with pytest.raises(IsOkError) as exc_info:
            Ok("yay").expect_err("hello")
        assert exc_info.value.result == Ok("yay")

    def test_unwrap(self) -> None:
        assert Ok("yay").unwrap() == "yay"
        with pytest.raises(IsNotOkError) as exc_info:
            Err("nay").unwrap()
        assert exc_info.value.result == Err("nay")

    def test_unwrap_err(self) -> None:
        assert Err("nay").unwrap_err() == "nay"
        with pytest.raises(IsOkError) as exc_info:
            Ok("yay").unwrap_err()
        assert exc_info.value.result == Ok("yay")

    def test_unwrap_or(self) -> None:
        assert Ok("yay").unwrap_or("some_default") == "yay"
        assert Err("nay").unwrap_or("another_default") == "another_default"

    def test_unwrap_or_else(self) -> None:
        assert Ok("yay").unwrap_or_else(str.upper) == "yay"
        assert Err("nay").unwrap_or_else(str.upper) == "NAY"

    def test_and_result(self) -> None:
        assert Ok(2).and_result(Ok(1)) == Ok(1)
        assert Ok(2).and_result(Err(1)) == Err(1)
        assert Err(1).and_result(Err(2)) == Err(1)
        assert Err(1).and_result(Ok(2)) == Err(1)

    def test_and_then(self) -> None:
        assert Ok(2).and_then(sq).and_then(sq).ok() == Some(16)
        assert Ok(2).and_then(sq).and_then(to_err).err() == Some(4)
        assert Ok(2).and_then(to_err).and_then(sq).err() == Some(2)
        assert Err(3).and_then(sq).and_then(sq).err() == Some(3)

        assert Ok(2).and_then(sq_lambda).and_then(sq_lambda).ok() == Some(16)
        assert Ok(2).and_then(sq_lambda).and_then(to_err_lambda).err() == Some(4)
        assert Ok(2).and_then(to_err_lambda).and_then(sq_lambda).err() == Some(2)
        assert Err(3).and_then(sq_lambda).and_then(sq_lambda).err() == Some(3)

    def test_or_result(self) -> None:
        assert Ok(2).or_result(Ok(1)) == Ok(2)
        assert Ok(2).or_result(Err(1)) == Ok(2)
        assert Err(1).or_result(Err(2)) == Err(2)
        assert Err(1).or_result(Ok(2)) == Ok(2)

    def test_or_else(self) -> None:
        assert Ok(2).or_else(sq).or_else(sq).ok() == Some(2)
        assert Ok(2).or_else(to_err).or_else(sq).ok() == Some(2)
        assert Err(3).or_else(sq).or_else(to_err).ok() == Some(9)
        assert Err(3).or_else(to_err).or_else(to_err).err() == Some(3)

        assert Ok(2).or_else(sq_lambda).or_else(sq).ok() == Some(2)
        assert Ok(2).or_else(to_err_lambda).or_else(sq_lambda).ok() == Some(2)
        assert Err(3).or_else(sq_lambda).or_else(to_err_lambda).ok() == Some(9)
        assert Err(3).or_else(to_err_lambda).or_else(to_err_lambda).err() == Some(3)

    def test_contains(self) -> None:
        assert Ok().contains(True) is True
        assert Ok(1).contains(1) is True
        assert Ok(1).contains(0) is False
        assert Err().contains(False) is False
        assert Err(1).contains(1) is False

    def test_contains_err(self) -> None:
        assert Ok().contains_err(True) is False
        assert Ok(1).contains_err(1) is False
        assert Err().contains_err(False) is True
        assert Err(1).contains_err(1) is True


def sq(i: int) -> Result[int, int]:
    return Ok(i * i)


def to_err(i: int) -> Result[int, int]:
    return Err(i)


# Lambda versions of the same functions, just for test/type coverage
sq_lambda: Callable[[int], Result[int, int]] = lambda i: Ok(i * i)
to_err_lambda: Callable[[int], Result[int, int]] = lambda i: Err(i)
