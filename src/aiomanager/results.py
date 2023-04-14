from __future__ import annotations

import abc
import typing as t

from typing_extensions import Final, TypeAlias

T = t.TypeVar("T")  # Success type
U = t.TypeVar("U")
E = t.TypeVar("E", covariant=True)  # Error type
F = t.TypeVar("F")
R = t.TypeVar("R")


SingletonT = t.TypeVar("SingletonT", bound="SingletonABC")


class SingletonABC(abc.ABCMeta):
    _instances: dict[t.Type[SingletonABC], SingletonABC] = {}
    __slots__ = ()

    def __call__(cls: t.Type[SingletonT], *args: t.Any, **kwargs: t.Any) -> SingletonT:  # type: ignore[misc]
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonABC, cls).__call__(*args, **kwargs)
        return cls._instances[cls]  # type: ignore[return-value]


class OptionABC(t.Generic[T], metaclass=abc.ABCMeta):
    __slots__ = ()

    @abc.abstractproperty
    def value(self) -> T:
        """Returns the contained `Some` value or raise an error if option is `Nothing`."""

    @abc.abstractmethod
    def __repr__(self) -> str:
        """String representation."""

    @abc.abstractmethod
    def __eq__(self, other: t.Any) -> bool:
        """Equality operator."""

    @abc.abstractmethod
    def __ne__(self, other: t.Any) -> bool:
        """Non-equality operator."""

    @abc.abstractmethod
    def __hash__(self) -> int:
        """Get result hash."""

    @abc.abstractmethod
    def __bool__(self) -> bool:
        """Boolean operator."""

    @abc.abstractmethod
    def __iter__(self) -> t.Iterator[T]:
        """Iterate over option value (yield a single value in case of Some, else raise an error)."""

    @abc.abstractmethod
    def __next__(self) -> T:
        """Return result value in case of Some else raise a StopIteration."""

    @abc.abstractmethod
    def is_some(self) -> t.Literal[True, False]:
        """Returns true if the option is a `Some` value."""

    @abc.abstractmethod
    def is_some_and(self, predicate: t.Callable[[T], bool]) -> bool:
        """Returns true if the option is a `Some` value."""

    @abc.abstractmethod
    def is_nothing(self) -> t.Literal[True, False]:
        """Returns true if the option is `Nothing`."""

    @abc.abstractmethod
    def expect(self, msg: str) -> T:
        """Returns the contained `Some` value or raise an error with message provided by `msg` argument."""

    @abc.abstractmethod
    def expect_nothing(self, msg: str) -> None:
        """Returns None if the option is `Nothing` or raise an error with message provided by `msg` argument."""

    @abc.abstractmethod
    def unwrap(self) -> T:
        """Returns the contained Some value or raise an error."""

    @abc.abstractmethod
    def unwrap_or(self, default: T) -> T:
        """Returns the contained Some value or a provided default."""

    @abc.abstractmethod
    def unwrap_or_else(self, func: t.Callable[[], T]) -> T:
        """Returns the contained Some value or computes it from a closure."""

    @abc.abstractmethod
    def map(self, func: t.Callable[[T], U]) -> Option[U]:
        """Maps an `Option[T]` to `Option[U]` by applying a function to a contained value (if Some)."""

    @abc.abstractmethod
    def inspect(self, func: t.Callable[[T], t.Any]) -> Option[T]:
        """Calls the provided closure with a reference to the contained value (if Some)."""

    @abc.abstractmethod
    def map_or(self, default: U, func: t.Callable[[T], U]) -> U:
        """Returns the provided default result (if `Nothing`), or applies a function to the contained value (if Some)."""

    @abc.abstractmethod
    def map_or_else(self, default: t.Callable[[], U], func: t.Callable[[T], U]) -> U:
        """Computes a default function result (if `Nothing`), or applies a different function to the contained value (if Some)."""

    @abc.abstractmethod
    def ok_or(self, err: F) -> Result[T, E | F]:
        """Transforms the Option[T] into a Result[T, E], mapping Some(v) to Ok(v) and `Nothing` to Err(err)."""

    @abc.abstractmethod
    def ok_or_else(self, err: t.Callable[[], E]) -> Result[T, E]:
        """Transforms the Option[T] into a Result[T, E], mapping Some(v) to Ok(v) and `Nothing` to Err(err())."""

    @abc.abstractmethod
    def and_option(self, other: Option[U]) -> Option[U]:
        """Returns `Nothing` if the option is `Nothing` or other is `Nothing`, otherwise returns other"""

    @abc.abstractmethod
    def and_then(self, func: t.Callable[[T], Option[U]]) -> Option[U]:
        """Returns `Nothing` if the option is `Nothing` or other is `Nothing`, otherwise calls func with the contained value"""

    @abc.abstractmethod
    def filter(self, predicate: t.Callable[[T], bool]) -> Option[T]:
        """Returns None if the option is None, otherwise calls predicate with the wrapped value and returns:

        - Some(t) if predicate returns true (where t is the wrapped value), and
        - None if predicate returns false.
        """

    @abc.abstractmethod
    def or_option(self, other: Option[T]) -> Option[T]:
        """Returns the option if it contains a value, otherwise returns other."""

    @abc.abstractmethod
    def or_else(self, func: t.Callable[[], Option[T]]) -> Option[T]:
        """Returns the option if it contains a value, otherwise calls provided function and return option."""

    @abc.abstractmethod
    def xor(self, other: Option[T]) -> Option[T]:
        """Returns Some if exactly one of self, other is Some, otherwise returns Nothing"""

    @abc.abstractmethod
    def contains(self, value: T) -> bool:
        """Return true, if option is Some and container value is equal to provided value"""

    @abc.abstractmethod
    def zip(self, other: Option[U]) -> Option[tuple[T, U]]:
        """Zips self with another Option.

        If self is Some(s) and other is Some(o), this method returns Some((s, o)). Otherwise, Nothing is returned.
        """

    @abc.abstractmethod
    def zip_with(self, other: Option[U], func: t.Callable[[T, U], R]) -> Option[R]:
        """Zips self and another Option with function func.

        If self is Some(s) and other is Some(o), this method returns Some(func(s, o)). Otherwise, Nothing is returned.
        """


class ResultABC(t.Generic[T, E], metaclass=abc.ABCMeta):
    """`Result[T, E]` is a type that represents either success (`Ok[T]`) or failure (`Err[E]`)."""

    __slots__ = ()

    @abc.abstractproperty
    def value(self) -> T | E:
        """Get result value."""

    @abc.abstractmethod
    def __repr__(self) -> str:
        """Result string representation."""

    @abc.abstractmethod
    def __eq__(self, other: t.Any) -> bool:
        """Equality operator."""

    @abc.abstractmethod
    def __ne__(self, other: t.Any) -> bool:
        """Non-equality operator."""

    @abc.abstractmethod
    def __bool__(self) -> t.Literal[True, False]:
        """Boolean operator."""

    @abc.abstractmethod
    def __hash__(self) -> int:
        """Result hash value."""

    @abc.abstractmethod
    def __iter__(self) -> t.Iterator[T]:
        """Iterate over result value (yield a single value in case of Ok, else raise an error)."""

    @abc.abstractmethod
    def __next__(self) -> T:
        """Return result value in case Ok else raise a StopIteration."""

    @abc.abstractmethod
    def is_ok(self) -> t.Literal[True, False]:
        """Returns true if the result is Ok."""

    @abc.abstractmethod
    def is_ok_and(self, predicate: t.Callable[[T], bool]) -> bool:
        """Returns true if the result is Ok and the value inside of it matches a predicate."""

    @abc.abstractmethod
    def is_err(self) -> t.Literal[True, False]:
        """Returns true if the result is Err."""

    @abc.abstractmethod
    def is_err_and(self, predicate: t.Callable[[E], bool]) -> bool:
        """Returns true if the result is Err and the value inside of it matches a predicate."""

    @abc.abstractmethod
    def ok(self) -> Option[T]:
        """Converts from `Result[T, E]` to `Option[T]`.

        Converts self into an `Option[T]`, discarding the error if any.
        """

    @abc.abstractmethod
    def err(self) -> Option[E]:
        """Converts from Result[T, E] to Option[E].

        Converts self into an Option[E], discarding the success value, if any.
        """

    @abc.abstractmethod
    def map(self, func: t.Callable[[T], U]) -> Result[U, E]:
        """Maps a `Result[T, E]` to `Result[U, E]` by applying a function to a contained `Ok` value, leaving an `Err` value untouched."""

    @abc.abstractmethod
    def map_err(self, func: t.Callable[[E], F]) -> Result[T, F]:
        """Maps a Result[T, E] to Result[T, F] by applying a function to a contained Err value, leaving an Ok value untouched."""

    @abc.abstractmethod
    def map_or(self, default: U, func: t.Callable[[T], U]) -> U:
        """Returns the provided default (if Err), or applies a function to the contained value (if Ok)."""

    @abc.abstractmethod
    def map_or_else(self, default: t.Callable[[], U], func: t.Callable[[T], U]) -> U:
        """Maps a Result[T, E] to U by applying fallback function default to a contained Err value, or function f to a contained Ok value."""

    @abc.abstractmethod
    def inspect(self, func: t.Callable[[T], t.Any]) -> Result[T, E]:
        """Calls the provided closure with a reference to the contained value (if Ok)."""

    @abc.abstractmethod
    def inspect_err(self, func: t.Callable[[E], t.Any]) -> Result[T, E]:
        """Calls the provided closure with a reference to the contained error (if Err)."""

    @abc.abstractmethod
    def expect(self, msg: str) -> T:
        """Returns the contained Ok value if Ok else raises an error with provided message."""

    @abc.abstractmethod
    def expect_err(self, msg: str) -> E:
        """Returns the contained Err value if result is Err else raise an error with provided message."""

    @abc.abstractmethod
    def unwrap(self) -> T:
        """Returns the contained Ok value if Ok else raises an error."""

    @abc.abstractmethod
    def unwrap_err(self) -> E:
        """Returns the contained Err value if Err else raises an error."""

    @abc.abstractmethod
    def unwrap_or(self, default: T) -> T:
        """Returns the contained Ok value or a provided default."""

    @abc.abstractmethod
    def unwrap_or_else(self, default: t.Callable[[E], T]) -> T:
        """Returns the contained Ok value or computes it from a closure."""

    @abc.abstractmethod
    def and_result(self, other: Result[U, E]) -> Result[U, E]:
        """Returns other if the result is Ok, otherwise forwarsd Err."""

    @abc.abstractmethod
    def and_then(self, func: t.Callable[[T], Result[U, E]]) -> Result[U, E]:
        """Calls func if the result is Ok, otherwise forwards Err"""

    @abc.abstractmethod
    def or_result(self, other: Result[T, F]) -> Result[T, F]:
        """Returns res if the result is Err, otherwise returns the Ok value."""

    @abc.abstractmethod
    def or_else(self, func: t.Callable[[E], Result[T, F]]) -> Result[T, F]:
        """Calls func if the result is Err, otherwise forward Ok."""

    @abc.abstractmethod
    def contains(self, value: t.Any) -> bool:
        """Returns true if the result is an Ok value containing the given value."""

    @abc.abstractmethod
    def contains_err(self, value: t.Any) -> bool:
        """Returns true if the result is an Err value containing the given value."""


class Some(OptionABC[T]):
    """
    A value that indicates presence of data and which stores arbitrary data for the return value.
    """

    _value: T
    __slots__ = ("_value", "_visited")
    __match_args__ = ("value",)

    @t.overload
    def __init__(self: Some[bool]) -> None:
        ...  # pragma: no cover

    @t.overload
    def __init__(self, value: T) -> None:
        ...  # pragma: no cover

    def __init__(self, value: t.Any = True) -> None:
        self._value = value
        self._visited = False

    @property
    def value(self) -> T:
        return self._value

    def __repr__(self) -> str:
        return "Some({})".format(repr(self._value))

    def __eq__(self, other: t.Any) -> bool:
        return isinstance(other, Some) and self.value == other.value

    def __ne__(self, other: t.Any) -> bool:
        return not (self == other)  # NOSONAR

    def __bool__(self) -> t.Literal[True]:
        return True

    def __hash__(self) -> int:
        return hash((True, self._value))

    def __iter__(self) -> t.Iterator[T]:
        self._visited = False
        return self

    def __next__(self) -> T:
        if not self._visited:
            self._visited = True
            return self._value
        raise StopIteration

    def is_some(self) -> t.Literal[True]:
        return True

    def is_some_and(self, predicate: t.Callable[[T], bool]) -> bool:
        return predicate(self._value)

    def is_nothing(self) -> t.Literal[False]:
        return False

    def expect(self, msg: str) -> T:
        return self._value

    def expect_nothing(self, msg: str) -> t.NoReturn:
        raise IsNotNothingError(self, msg)

    def unwrap(self) -> T:
        return self._value

    def unwrap_or(self, default: object) -> T:
        return self._value

    def unwrap_or_else(self, func: t.Callable[[], T]) -> T:
        return self._value

    def map(self, func: t.Callable[[T], U]) -> Some[U]:
        return Some(func(self._value))

    def inspect(self, func: t.Callable[[T], t.Any]) -> Some[T]:
        func(self._value)
        return self

    def map_or(self, default: object, func: t.Callable[[T], U]) -> U:
        return func(self._value)

    def map_or_else(self, default: object, func: t.Callable[[T], U]) -> U:
        return func(self._value)

    def ok_or(self, err: object) -> Ok[T]:
        return Ok(self._value)

    def ok_or_else(self, err: object) -> Ok[T]:
        return Ok(self._value)

    def and_option(self, other: Option[U]) -> Option[U]:
        if other:
            return other
        return NOTHING

    def and_then(self, func: t.Callable[[T], Option[U]]) -> Option[U]:
        return func(self._value)

    def filter(self, predicate: t.Callable[[T], bool]) -> Option[T]:
        return self if predicate(self._value) else NOTHING

    def or_option(self, other: object) -> Some[T]:
        return self

    def or_else(self, func: object) -> Some[T]:
        return self

    def xor(self, other: Option[T]) -> Option[T]:
        return NOTHING if other else self

    def contains(self, value: T) -> bool:
        return self._value == value

    def zip(self, other: Option[U]) -> Option[tuple[T, U]]:
        if other:
            return Some((self._value, other._value))
        return NOTHING

    def zip_with(self, other: Option[U], func: t.Callable[[T, U], R]) -> Option[R]:
        if other:
            return Some(func(self._value, other._value))
        return NOTHING


class Nothing(OptionABC[t.NoReturn], metaclass=SingletonABC):
    """
    A value that signifies failure and which stores arbitrary data for the error.
    """

    @property
    def value(self) -> t.NoReturn:
        raise IsNothingError("Nothing objects do not have value")

    def __repr__(self) -> str:
        return "Nothing()"

    def __eq__(self, other: t.Any) -> bool:
        return self is other

    def __ne__(self, other: t.Any) -> bool:
        return self is not other

    def __hash__(self) -> int:
        return hash((False, "Nothing"))

    def __bool__(self) -> t.Literal[False]:
        return False

    def __iter__(self) -> t.Iterator[t.NoReturn]:
        return self

    def __next__(self) -> t.NoReturn:
        raise StopIteration

    def is_some(self) -> t.Literal[False]:
        return False

    def is_some_and(self, predicate: t.Callable[[t.Any], bool]) -> t.Literal[False]:
        return False

    def is_nothing(self) -> t.Literal[True]:
        return True

    def expect(self, msg: str) -> t.NoReturn:
        raise IsNothingError(msg)

    def expect_nothing(self, msg: str) -> None:
        return None

    def unwrap(self) -> t.NoReturn:
        raise IsNothingError("Called `Maybe.unwrap()` on an `Nothing` value")

    def unwrap_or(self, default: U) -> U:
        return default

    def unwrap_or_else(self, func: t.Callable[[], U]) -> U:
        return func()

    def map(self, func: object) -> Nothing:
        return self

    def inspect(self, func: object) -> Nothing:
        return self

    def map_or(self, default: U, func: object) -> U:
        return default

    def map_or_else(self, default: t.Callable[[], U], func: object) -> U:
        return default()

    def ok_or(self, err: F) -> Err[F]:
        return Err(err)

    def ok_or_else(self, err: t.Callable[[], E]) -> Err[E]:
        return Err(err())

    def and_option(self, other: object) -> Nothing:
        return self

    def and_then(self, func: object) -> Nothing:
        return self

    def filter(self, predicate: object) -> Nothing:
        return self

    def or_option(self, other: Option[U]) -> Option[U]:
        return other

    def or_else(self, func: t.Callable[[], Option[U]]) -> Option[U]:
        return func()

    def xor(self, other: Option[U]) -> Option[U]:
        return other

    def contains(self, other: object) -> t.Literal[False]:
        return False

    def zip(self, other: object) -> Nothing:
        return self

    def zip_with(self, other: object, func: object) -> Option[R]:
        return self


class Ok(ResultABC[T, t.NoReturn]):
    """
    A value that indicates success and which stores arbitrary data for the return value.
    """

    _value: T
    __slots__ = ("_value", "_visited")
    __match_args__ = ("value",)

    @t.overload
    def __init__(self, value: T) -> None:
        ...  # pragma: no cover

    @t.overload
    def __init__(self: Ok[t.Literal[True]]) -> None:
        ...  # pragma: no cover

    def __init__(self, value: t.Any = True) -> None:
        self._value = value
        self._visited = False

    @property
    def value(self) -> T:
        return self._value

    def __repr__(self) -> str:
        return "Ok({})".format(repr(self._value))

    def __eq__(self, other: t.Any) -> bool:
        return isinstance(other, Ok) and self.value == other.value

    def __ne__(self, other: t.Any) -> bool:
        return not (self == other)  # NOSONAR

    def __bool__(self) -> t.Literal[True]:
        return True

    def __hash__(self) -> int:
        return hash((True, self._value))

    def __iter__(self) -> t.Iterator[T]:
        self._visited = False
        return self

    def __next__(self) -> T:
        if self._visited:
            raise StopIteration
        self._visited = True
        return self._value

    def is_ok(self) -> t.Literal[True]:
        return True

    def is_ok_and(self, predicate: t.Callable[[T], bool]) -> bool:
        return predicate(self._value)

    def is_err(self) -> t.Literal[False]:
        return False

    def is_err_and(self, predicate: object) -> t.Literal[False]:
        return False

    def ok(self) -> Some[T]:
        return Some(self._value)

    def err(self) -> Nothing:
        return NOTHING

    def map(self, func: t.Callable[[T], U]) -> Ok[U]:
        return Ok(func(self._value))

    def map_or(self, default: object, func: t.Callable[[T], U]) -> U:
        return func(self._value)

    def map_or_else(self, default: object, func: t.Callable[[T], U]) -> U:
        return func(self._value)

    def map_err(self, func: object) -> Ok[T]:
        return self

    def inspect(self, func: t.Callable[[T], t.Any]) -> Ok[T]:
        func(self._value)
        return self

    def inspect_err(self, func: object) -> Ok[T]:
        return self

    def expect(self, msg: str) -> T:
        """
        Return the value.
        """
        return self._value

    def unwrap(self) -> T:
        return self._value

    def expect_err(self, msg: str) -> t.NoReturn:
        raise IsOkError(self, msg)

    def unwrap_err(self) -> t.NoReturn:
        raise IsOkError(self, "Called `Result.unwrap_err()` on an `Ok` value")

    def and_result(self, other: Result[U, E]) -> Result[U, E]:
        return other

    def and_then(self, func: t.Callable[[T], Result[U, E]]) -> Result[U, E]:
        return func(self._value)

    def or_result(self, other: object) -> Ok[T]:
        return self

    def or_else(self, other: object) -> Ok[T]:
        return self

    def unwrap_or(self, default: object) -> T:
        return self._value

    def unwrap_or_else(self, default: object) -> T:
        return self._value

    def contains(self, value: T) -> bool:
        return self._value == value

    def contains_err(self, value: object) -> t.Literal[False]:
        return False


ErrT = t.TypeVar("ErrT", bound="Err[t.Any]")


class Err(ResultABC[t.NoReturn, E]):
    """
    A value that signifies failure and which stores arbitrary data for the error.
    """

    _value: E
    __slots__ = "_value"
    __match_args__ = ("value",)

    @t.overload
    def __init__(self, value: E) -> None:
        ...  # pragma: no cover

    @t.overload
    def __init__(self: Err[bool]) -> None:
        ...  # pragma: no cover

    def __init__(self, value: t.Any = False) -> None:
        self._value = value

    @property
    def value(self) -> E:
        return self._value

    def __repr__(self) -> str:
        return "Err({})".format(repr(self._value))

    def __eq__(self, other: t.Any) -> bool:
        return isinstance(other, Err) and self.value == other.value

    def __ne__(self, other: t.Any) -> bool:
        return not (self == other)  # NOSONAR

    def __hash__(self) -> int:
        return hash((False, self._value))

    def __bool__(self) -> t.Literal[False]:
        return False

    def __iter__(self: ErrT) -> ErrT:
        return self

    def __next__(self) -> t.NoReturn:
        raise StopIteration

    def is_ok(self) -> t.Literal[False]:
        return False

    def is_ok_and(self, predicate: object) -> t.Literal[False]:
        return False

    def is_err(self) -> t.Literal[True]:
        return True

    def is_err_and(self, predicate: t.Callable[[E], bool]) -> bool:
        return predicate(self._value)

    def ok(self) -> Nothing:
        return NOTHING

    def err(self) -> Some[E]:
        return Some(self._value)

    def map(self, func: object) -> Err[E]:
        return self

    def map_or(self, default: U, func: object) -> U:
        return default

    def map_or_else(self, default: t.Callable[[], U], func: object) -> U:
        return default()

    def map_err(self, func: t.Callable[[E], F]) -> Err[F]:
        return Err(func(self._value))

    def inspect(self, func: object) -> Result[T, E]:
        return self

    def inspect_err(self, func: t.Callable[[E], t.Any]) -> Result[T, E]:
        func(self._value)
        return self

    def expect(self, message: str) -> t.NoReturn:
        raise IsNotOkError(self, message)

    def expect_err(self, msg: str) -> E:
        return self._value

    def unwrap(self) -> t.NoReturn:
        raise IsNotOkError(self, "Called `Result.unwrap()` on an `Err` value")

    def unwrap_err(self) -> E:
        return self._value

    def unwrap_or(self, default: T) -> T:
        return default

    def unwrap_or_else(self, default: t.Callable[[E], T]) -> T:
        return default(self._value)

    def and_result(self, other: object) -> Err[E]:
        return self

    def and_then(self, other: object) -> Err[E]:
        return self

    def or_result(self, other: Result[T, F]) -> Result[T, F]:
        return other

    def or_else(self, func: t.Callable[[E], Result[T, F]]) -> Result[T, F]:
        return func(self._value)

    def contains(self, value: object) -> t.Literal[False]:
        return False

    def contains_err(self, value: object) -> bool:
        return self._value == value


# define Result as a generic type alias for use
# in type annotations
Result: TypeAlias = t.Union[Ok[T], Err[E]]
"""
A simple `Result` type inspired by Rust.
Not all methods (https://doc.rust-lang.org/std/result/enum.Result.html)
have been implemented, only the ones that make sense in the Python context.
"""


ResultType: Final = (Ok, Err)
"""
A type to use in `isinstance` checks.
This is purely for convenience sake, as you could also just write `isinstance(res, (Ok, Err))
"""

# define Option as a generic type alias for use
# in type annotations
Option: TypeAlias = t.Union[Some[T], Nothing]
"""
A simple `Option` type inspired by Rust.
Not all methods (https://doc.rust-lang.org/std/option/enum.Option.html)
have been implemented, only the ones that make sense in the Python context.
"""

OptionType: Final = (Some, Nothing)
"""
A type to use in `isinstance` checks.
This is purely for convenience sake, as you could also just write `isinstance(res, (Some, Nothing))
"""

# create Nothing() singleton
NOTHING = Nothing()


# Define errors
class UnwrapError(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)


class OptionError(UnwrapError):
    _option: Option[t.Any]

    def __init__(self, option: Option[t.Any], message: str) -> None:
        self._option = option
        super().__init__(message)

    @property
    def option(self) -> Option[t.Any]:
        """Returns the original option"""
        return self._option


class ResultError(UnwrapError):
    _result: Result[t.Any, t.Any]

    def __init__(self, result: Result[t.Any, t.Any], message: str) -> None:
        self._result = result
        super().__init__(message)

    @property
    def result(self) -> Result[t.Any, t.Any]:
        """Returns the original result."""
        return self._result


class IsNotNothingError(OptionError):
    _option: Some[t.Any]

    def __init__(self, option: Some[t.Any], message: str) -> None:
        super().__init__(option, message)


class IsNothingError(OptionError):
    _option: Nothing

    def __init__(self, message: str) -> None:
        super().__init__(NOTHING, message)


class IsOkError(ResultError):
    _result: Ok[t.Any]

    def __init__(self, result: Ok[t.Any], message: str) -> None:
        super().__init__(result, message)


class IsNotOkError(ResultError):
    _result: Err[t.Any]

    def __init__(self, result: Err[t.Any], message: str) -> None:
        super().__init__(result, message)
