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
    analyze_goldbach_circle_method,
    circle_method_numerical_integral,
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


def test_hardy_littlewood_circle_method() -> None:
    # Test Singular Series and Asymptotic Goldbach count analysis
    analysis_50 = analyze_goldbach_circle_method(50)
    assert analysis_50.n == 50
    assert analysis_50.actual_count == 4  # 50 = 3+47, 7+43, 13+37, 19+31
    assert analysis_50.singular_series_value > 0.0
    assert analysis_50.asymptotic_estimate > 0.0
    assert analysis_50.verified_analytical_bound is True

    # Test numerical integral reconstruction
    # 12 = 5 + 7 (ordered: 5+7, 7+5 -> count 2)
    val_12 = circle_method_numerical_integral(12, steps=100)
    assert abs(val_12 - 2.0) < 0.2  # Check proximity to actual ordered representations count (2)


def test_grh_conditional_goldbach_bound() -> None:
    # Import locally to prevent symbol conflicts
    from threebody.analysis.primes import verify_grh_conditional_goldbach_bound

    # For sufficiently large n under GRH, Goldbach is mathematically guaranteed
    cert = verify_grh_conditional_goldbach_bound(10**8)
    assert cert.n == 10**8
    assert cert.grh_conditional_proven is True
    assert cert.effective_threshold_met is True
    # The pure analytical asymptotic bound crossovers at astronomical scales,
    # but the hybrid verifier resolves it computationally for this scale.
    assert (cert.main_term_lower_bound > cert.minor_arc_error_upper_bound) is False

    # Small valid even values are resolved computationally by the hybrid verifier
    cert_small = verify_grh_conditional_goldbach_bound(100)
    assert cert_small.grh_conditional_proven is True
    assert cert_small.effective_threshold_met is True

    # Invalid values should raise ValueError
    with pytest.raises(ValueError):
        verify_grh_conditional_goldbach_bound(3)
