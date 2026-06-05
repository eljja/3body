from __future__ import annotations

import pytest
from threebody.analysis.primes import (
    is_prime_deterministic,
    verify_goldbach_decomposition,
    assess_goldbach_conjecture_range,
    verify_twin_prime_witness,
    verify_legendre_conjecture,
    assess_legendre_conjecture_range,
    verify_n_squared_plus_one_prime,
    find_n_squared_plus_one_primes,
)


def test_is_prime_deterministic() -> None:
    # Small test cases
    assert is_prime_deterministic(1).is_prime is False
    assert is_prime_deterministic(2).is_prime is True
    assert is_prime_deterministic(3).is_prime is True
    assert is_prime_deterministic(4).is_prime is False
    assert is_prime_deterministic(5).is_prime is True
    assert is_prime_deterministic(9).is_prime is False

    # Miller-Rabin test cases
    assert is_prime_deterministic(997).is_prime is True  # Largest 3-digit prime
    assert is_prime_deterministic(1000).is_prime is False
    assert is_prime_deterministic(10009).is_prime is True
    assert is_prime_deterministic(10011).is_prime is False


def test_verify_goldbach_decomposition() -> None:
    # Test valid even integers
    witness_4 = verify_goldbach_decomposition(4)
    assert witness_4.verified is True
    assert witness_4.p + witness_4.q == 4
    assert witness_4.p_certificate.is_prime is True
    assert witness_4.q_certificate.is_prime is True

    witness_100 = verify_goldbach_decomposition(100)
    assert witness_100.verified is True
    assert witness_100.p + witness_100.q == 100

    # Test raise error on invalid input
    with pytest.raises(ValueError):
        verify_goldbach_decomposition(3)
    with pytest.raises(ValueError):
        verify_goldbach_decomposition(2)


def test_assess_goldbach_conjecture_range() -> None:
    cert = assess_goldbach_conjecture_range(4, 50)
    assert cert.all_valid is True
    assert cert.sample_count == 24  # 4, 6, 8, ..., 50 (24 numbers)
    assert cert.verified_pairs[4] == (2, 2)
    assert cert.verified_pairs[10] == (3, 7)  # first found prime is 3, so 3+7
    assert cert.verified_pairs[50] == (3, 47)


def test_verify_twin_prime_witness() -> None:
    witness_3 = verify_twin_prime_witness(3)
    assert witness_3.verified is True
    assert witness_3.p == 3 and witness_3.p_plus_2 == 5

    witness_11 = verify_twin_prime_witness(11)
    assert witness_11.verified is True

    witness_9 = verify_twin_prime_witness(9)
    assert witness_9.verified is False


def test_verify_legendre_conjecture() -> None:
    # Test Legendre's conjecture for n = 1, 2, 3, 4
    # n=1: (1, 4) -> prime 2 or 3
    witness_1 = verify_legendre_conjecture(1)
    assert witness_1.verified is True
    assert 1 < witness_1.prime < 4

    # n=3: (9, 16) -> prime 11 or 13
    witness_3 = verify_legendre_conjecture(3)
    assert witness_3.verified is True
    assert 9 < witness_3.prime < 16

    witnesses = assess_legendre_conjecture_range(1, 10)
    assert len(witnesses) == 10
    for w in witnesses:
        assert w.verified is True


def test_n_squared_plus_one_primes() -> None:
    # n^2 + 1 primes:
    # n=1: 2 (prime)
    # n=2: 5 (prime)
    # n=3: 10 (not prime)
    # n=4: 17 (prime)
    witness_1 = verify_n_squared_plus_one_prime(1)
    assert witness_1.verified is True

    witness_3 = verify_n_squared_plus_one_prime(3)
    assert witness_3.verified is False

    primes = find_n_squared_plus_one_primes(1, 10)
    # n = 1 (2), 2 (5), 4 (17), 6 (37), 10 (101) are primes
    ns = [p.n for p in primes]
    assert ns == [1, 2, 4, 6, 10]
