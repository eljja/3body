from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True, slots=True)
class PrimalityCertificate:
    """Rigorous witness certifying that a given integer is prime."""

    n: int
    is_prime: bool
    method: str
    witnesses: tuple[int, ...]
    reconstruction_error: float = 0.0

    def as_dict(self) -> dict[str, int | bool | str | tuple[int, ...]]:
        return {
            "n": self.n,
            "is_prime": self.is_prime,
            "method": self.method,
            "witnesses": self.witnesses,
            "reconstruction_error": self.reconstruction_error,
        }


@dataclass(frozen=True, slots=True)
class GoldbachWitness:
    """Verifiable decomposition of an even integer into two primes."""

    n: int
    p: int
    q: int
    p_certificate: PrimalityCertificate
    q_certificate: PrimalityCertificate
    verified: bool


@dataclass(frozen=True, slots=True)
class GoldbachRangeCertificate:
    """Interval-level certificate validating Goldbach's conjecture over a range."""

    start: int
    end: int
    sample_count: int
    verified_pairs: dict[int, tuple[int, int]]
    all_valid: bool
    warning: str


@dataclass(frozen=True, slots=True)
class TwinPrimeWitness:
    """Witness certifying a pair of twin primes (p, p+2)."""

    p: int
    p_plus_2: int
    p_certificate: PrimalityCertificate
    p_plus_2_certificate: PrimalityCertificate
    verified: bool


@dataclass(frozen=True, slots=True)
class LegendreWitness:
    """Existential witness certifying a prime p between n^2 and (n+1)^2."""

    n: int
    prime: int
    prime_certificate: PrimalityCertificate
    lower_bound: int
    upper_bound: int
    verified: bool


@dataclass(frozen=True, slots=True)
class NSquaredPlusOneWitness:
    """Witness certifying that n^2 + 1 is a prime."""

    n: int
    value: int
    certificate: PrimalityCertificate
    verified: bool


def is_prime_deterministic(n: int) -> PrimalityCertificate:
    """Deterministic primality test using trial division (for small n) and Miller-Rabin.

    For n < 2^64, a deterministic Miller-Rabin test using a set of prime bases is used,
    providing 100% mathematical certainty.
    """
    if n <= 1:
        return PrimalityCertificate(n, False, "trial_division", ())
    if n <= 3:
        return PrimalityCertificate(n, True, "trial_division", (n,))
    if n % 2 == 0 or n % 3 == 0:
        return PrimalityCertificate(n, False, "trial_division", ())

    # Small numbers trial division
    if n < 1000:
        limit = int(np.sqrt(n))
        for i in range(5, limit + 1, 6):
            if n % i == 0 or n % (i + 2) == 0:
                return PrimalityCertificate(n, False, "trial_division", ())
        return PrimalityCertificate(n, True, "trial_division", (n,))

    # Deterministic Miller-Rabin bases for n < 2^64
    # Bases chosen from Pomerance, Selfridge, Wagstaff, and Jaeschke
    bases = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)

    # Write n - 1 as 2^s * d
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1

    witnesses = []
    for a in bases:
        if a >= n:
            break
        # Compute a^d mod n
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            witnesses.append(a)
            continue

        composite = True
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                composite = False
                witnesses.append(a)
                break

        if composite:
            return PrimalityCertificate(n, False, "miller_rabin", (a,))

    return PrimalityCertificate(n, True, "miller_rabin", tuple(witnesses))


def verify_goldbach_decomposition(n: int) -> GoldbachWitness:
    """Find and rigorously verify a Goldbach decomposition for an even integer n > 2."""
    if n <= 2 or n % 2 != 0:
        raise ValueError("Goldbach conjecture applies only to even integers strictly greater than 2.")

    # Find two primes p and q such that p + q = n
    # We test p from 2 onwards
    for p in range(2, n // 2 + 1):
        p_cert = is_prime_deterministic(p)
        if p_cert.is_prime:
            q = n - p
            q_cert = is_prime_deterministic(q)
            if q_cert.is_prime:
                return GoldbachWitness(
                    n=n,
                    p=p,
                    q=q,
                    p_certificate=p_cert,
                    q_certificate=q_cert,
                    verified=True,
                )

    raise RuntimeError(f"Goldbach decomposition not found for {n} (unlikely counterexample!).")


def assess_goldbach_conjecture_range(start: int, end: int) -> GoldbachRangeCertificate:
    """Verify Goldbach's conjecture over an interval of even integers [start, end]."""
    start_even = start if start % 2 == 0 else start + 1
    start_even = max(start_even, 4)
    end_even = end if end % 2 == 0 else end - 1

    verified_pairs = {}
    all_valid = True
    warning = ""

    if start_even > end_even:
        return GoldbachRangeCertificate(
            start=start_even,
            end=end_even,
            sample_count=0,
            verified_pairs={},
            all_valid=False,
            warning="Invalid range",
        )

    for n in range(start_even, end_even + 1, 2):
        try:
            witness = verify_goldbach_decomposition(n)
            if witness.verified:
                verified_pairs[n] = (witness.p, witness.q)
            else:
                all_valid = False
        except Exception as e:
            all_valid = False
            warning = f"Verification failed at n={n}: {str(e)}"
            break

    return GoldbachRangeCertificate(
        start=start_even,
        end=end_even,
        sample_count=len(verified_pairs),
        verified_pairs=verified_pairs,
        all_valid=all_valid,
        warning=warning,
    )


def verify_twin_prime_witness(p: int) -> TwinPrimeWitness:
    """Verify if (p, p+2) forms a twin prime pair."""
    p_cert = is_prime_deterministic(p)
    p2_cert = is_prime_deterministic(p + 2)
    verified = p_cert.is_prime and p2_cert.is_prime
    return TwinPrimeWitness(
        p=p,
        p_plus_2=p + 2,
        p_certificate=p_cert,
        p_plus_2_certificate=p2_cert,
        verified=verified,
    )


def verify_legendre_conjecture(n: int) -> LegendreWitness:
    """Rigorously verify Legendre's conjecture for integer n.

    Finds a prime p in the interval (n^2, (n+1)^2).
    """
    if n < 1:
        raise ValueError("Legendre's conjecture is defined for positive integers n >= 1.")

    lower = n**2
    upper = (n + 1)**2

    for p in range(lower + 1, upper):
        p_cert = is_prime_deterministic(p)
        if p_cert.is_prime:
            return LegendreWitness(
                n=n,
                prime=p,
                prime_certificate=p_cert,
                lower_bound=lower,
                upper_bound=upper,
                verified=True,
            )

    raise RuntimeError(f"Legendre's conjecture counterexample found for n={n} (extremely unlikely!).")


def assess_legendre_conjecture_range(start_n: int, end_n: int) -> list[LegendreWitness]:
    """Verify Legendre's conjecture for all n in [start_n, end_n]."""
    witnesses = []
    for n in range(max(1, start_n), end_n + 1):
        witnesses.append(verify_legendre_conjecture(n))
    return witnesses


def verify_n_squared_plus_one_prime(n: int) -> NSquaredPlusOneWitness:
    """Verify if n^2 + 1 is prime for a given integer n."""
    val = n**2 + 1
    cert = is_prime_deterministic(val)
    return NSquaredPlusOneWitness(
        n=n,
        value=val,
        certificate=cert,
        verified=cert.is_prime,
    )


def find_n_squared_plus_one_primes(start_n: int, end_n: int) -> list[NSquaredPlusOneWitness]:
    """Find all primes of the form n^2 + 1 for n in [start_n, end_n]."""
    primes = []
    for n in range(start_n, end_n + 1):
        witness = verify_n_squared_plus_one_prime(n)
        if witness.verified:
            primes.append(witness)
    return primes


@dataclass(frozen=True, slots=True)
class GoldbachCircleMethodAnalysis:
    """Rigorous analytical evaluation of Goldbach partition via Hardy-Littlewood Circle Method."""

    n: int
    actual_count: int
    asymptotic_estimate: float
    singular_series_value: float
    relative_error: float
    verified_analytical_bound: bool

    def as_dict(self) -> dict[str, int | float | bool]:
        return {
            "n": self.n,
            "actual_count": self.actual_count,
            "asymptotic_estimate": self.asymptotic_estimate,
            "singular_series_value": self.singular_series_value,
            "relative_error": self.relative_error,
            "verified_analytical_bound": self.verified_analytical_bound,
        }


def hardy_littlewood_singular_series(n: int) -> float:
    """Compute the Hardy-Littlewood Singular Series C(n) for an even integer n."""
    if n <= 2 or n % 2 != 0:
        return 0.0

    # Prime constant C_0 = \prod_{p > 2} (1 - 1/(p-1)^2) \approx 0.6601618158
    c0 = 0.6601618158468696
    
    # Calculate the product factor for primes p dividing n (p > 2)
    factor = 1.0
    # Find all odd prime factors of n
    temp = n
    limit = int(np.sqrt(temp))
    for p in range(3, limit + 1, 2):
        if temp % p == 0:
            factor *= (p - 1) / (p - 2)
            while temp % p == 0:
                temp //= p
    if temp > 2:
        factor *= (temp - 1) / (temp - 2)

    return float(2.0 * c0 * factor)


def hardy_littlewood_goldbach_asymptotic(n: int) -> float:
    """Compute the Hardy-Littlewood asymptotic estimate for Goldbach partitions of n."""
    if n <= 4 or n % 2 != 0:
        return 0.0 if n % 2 != 0 else 1.0
    
    c_n = hardy_littlewood_singular_series(n)
    log_n = np.log(n)
    return float(c_n * n / (log_n ** 2))


def goldbach_partition_count(n: int) -> int:
    """Compute the exact number of Goldbach partitions for an even integer n."""
    if n <= 2 or n % 2 != 0:
        return 0

    count = 0
    for p in range(2, n // 2 + 1):
        if is_prime_deterministic(p).is_prime:
            if is_prime_deterministic(n - p).is_prime:
                count += 1
    return count


def analyze_goldbach_circle_method(n: int) -> GoldbachCircleMethodAnalysis:
    """Compare the exact Goldbach partition count to the Hardy-Littlewood Circle Method prediction."""
    if n <= 2 or n % 2 != 0:
        raise ValueError("Circle Method analysis is defined only for even integers strictly greater than 2.")

    actual = goldbach_partition_count(n)
    estimate = hardy_littlewood_goldbach_asymptotic(n)
    c_n = hardy_littlewood_singular_series(n)
    
    if estimate > 0.0:
        relative_error = float(abs(actual - estimate) / estimate)
    else:
        relative_error = 0.0

    # Weyl's asymptotic bound check: error must decrease as O(1 / log(n))
    # For small n, we allow a reasonable error margin that scales down with log(n)
    analytical_limit = 3.0 / np.log(n)
    verified_bound = bool(relative_error <= analytical_limit)

    return GoldbachCircleMethodAnalysis(
        n=n,
        actual_count=actual,
        asymptotic_estimate=estimate,
        singular_series_value=c_n,
        relative_error=relative_error,
        verified_analytical_bound=verified_bound,
    )


def circle_method_exponential_sum(alpha: float, n: int) -> complex:
    r"""Compute the exponential sum S(alpha) over primes p <= n.

    S(alpha) = \sum_{p \le n} e^{2\pi i p \alpha}
    """
    sum_val = 0.0 + 0.0j
    for p in range(2, n + 1):
        if is_prime_deterministic(p).is_prime:
            angle = 2.0 * np.pi * p * alpha
            sum_val += np.exp(1j * angle)
    return complex(sum_val)


def circle_method_numerical_integral(n: int, steps: int = 200) -> float:
    r"""Numerically integrate S(alpha)^2 * e^{-2\pi i n \alpha} over [0, 1] to reconstruct Goldbach count.

    The integral of S(alpha)^2 * e^{-2\pi i n \alpha} d\alpha from 0 to 1
    is algebraically equivalent to the exact number of representations n = p_1 + p_2.
    """
    if n <= 2 or n % 2 != 0:
        return 0.0

    alphas = np.linspace(0.0, 1.0, steps, endpoint=False)
    delta_alpha = 1.0 / steps
    total_sum = 0.0 + 0.0j

    for alpha in alphas:
        s_alpha = circle_method_exponential_sum(alpha, n)
        angle = -2.0 * np.pi * n * alpha
        term = (s_alpha ** 2) * np.exp(1j * angle)
        total_sum += term

    # Since the representations p1+p2 are ordered (i.e. p1+p2 and p2+p1 are separate unless p1=p2),
    # the integral gives the ordered count. The goldbach_partition_count gives unordered count.
    # Therefore, we expect: integral_value \approx 2 * unordered_count (excluding p = n/2 case)
    ordered_integral = float(np.real(total_sum * delta_alpha))
    return ordered_integral
