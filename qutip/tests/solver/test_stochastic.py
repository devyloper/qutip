import pytest
import numpy as np
from qutip import (
    mesolve, liouvillian, QobjEvo, spre, spost,
    destroy, coherent, qeye, fock_dm, num
)
from qutip.solver.stochastic import smesolve, ssesolve, SMESolver, SSESolver
from qutip.core import data as _data


def f(t, w):
    return w * t

def _make_system(N, system):
    gamma = 0.25
    a = destroy(N)

    if system == "simple":
        H = a.dag() * a
        sc_ops = [np.sqrt(gamma) * a]

    elif system == "2 c_ops":
        H = QobjEvo([a.dag() * a])
        sc_ops = [np.sqrt(gamma) * a, gamma * a * a]

    elif system == "H td":
        H = [[a.dag() * a, f]]
        sc_ops = [np.sqrt(gamma) * QobjEvo(a)]

    elif system == "complex":
        H = [a.dag() * a + a.dag() + a]
        sc_ops = [np.sqrt(gamma) * a, gamma * a * a]

    elif system == "c_ops td":
        H = [a.dag() * a]
        sc_ops = [[np.sqrt(gamma) * a, f]]

    return H, sc_ops


@pytest.mark.parametrize("system", [
    "simple", "2 c_ops", "H td", "complex", "c_ops td",
])
@pytest.mark.parametrize("heterodyne", [True, False])
def test_smesolve(heterodyne, system):
    "Stochastic: smesolve: homodyne, time-dependent H"
    tol = 0.05
    N = 4
    ntraj = 20

    H, sc_ops = _make_system(N, system)
    c_ops = [destroy(N)]
    psi0 = coherent(N, 0.5)
    a = destroy(N)
    e_ops = [a.dag() * a, a + a.dag(), (-1j)*(a - a.dag())]

    times = np.linspace(0, 0.1, 21)
    res_ref = mesolve(H, psi0, times, c_ops + sc_ops, e_ops, args={"w": 2})

    options = {
        "store_measurement": False,
        "map": "serial",
    }

    res = smesolve(
        H, psi0, times, sc_ops=sc_ops, e_ops=e_ops, c_ops=c_ops,
        ntraj=ntraj, args={"w": 2}, options=options, heterodyne=heterodyne,
        seeds=1,
    )

    for idx in range(len(e_ops)):
        np.testing.assert_allclose(
            res.expect[idx], res_ref.expect[idx], rtol=tol, atol=tol
        )


@pytest.mark.parametrize("heterodyne", [True, False])
@pytest.mark.parametrize("method", SMESolver.avail_integrators().keys())
def test_smesolve_methods(method, heterodyne):
    "Stochastic: smesolve: homodyne, time-dependent H"
    tol = 0.05
    N = 4
    ntraj = 20
    system = "simple"

    H, sc_ops = _make_system(N, system)
    c_ops = [destroy(N)]
    psi0 = coherent(N, 0.5)
    a = destroy(N)
    e_ops = [a.dag() * a, a + a.dag(), (-1j)*(a - a.dag())]

    times = np.linspace(0, 0.1, 21)
    res_ref = mesolve(H, psi0, times, c_ops + sc_ops, e_ops, args={"w": 2})

    options = {
        "store_measurement": True,
        "map": "serial",
        "method": method,
    }

    res = smesolve(
        H, psi0, times, sc_ops=sc_ops, e_ops=e_ops, c_ops=c_ops,
        ntraj=ntraj, args={"w": 2}, options=options, heterodyne=heterodyne,
        seeds=list(range(ntraj)),
    )

    for idx in range(len(e_ops)):
        np.testing.assert_allclose(
            res.expect[idx], res_ref.expect[idx], rtol=tol, atol=tol
        )

    assert len(res.measurement) == ntraj

    if heterodyne:
        assert all([
            dw.shape == (len(sc_ops), 2, len(times)-1)
            for dw in res.dW
        ])
        assert all([
            w.shape == (len(sc_ops), 2, len(times))
            for w in res.wiener_process
        ])
        assert all([
            m.shape == (len(sc_ops), 2, len(times)-1)
            for m in res.measurement
        ])
    else:
        assert all([
            dw.shape == (len(sc_ops), len(times)-1)
            for dw in res.dW
        ])
        assert all([
            w.shape == (len(sc_ops), len(times))
            for w in res.wiener_process
        ])
        assert all([
            m.shape == (len(sc_ops), len(times)-1)
            for m in res.measurement
        ])


@pytest.mark.parametrize("system", [
    "simple", "2 c_ops", "H td", "complex", "c_ops td",
])
@pytest.mark.parametrize("heterodyne", [True, False])
def test_ssesolve(heterodyne, system):
    "Stochastic: smesolve: homodyne, time-dependent H"
    tol = 0.1
    N = 4
    ntraj = 20

    H, sc_ops = _make_system(N, system)
    psi0 = coherent(N, 0.5)
    a = destroy(N)
    e_ops = [a.dag() * a, a + a.dag(), (-1j)*(a - a.dag())]

    times = np.linspace(0, 0.1, 21)
    res_ref = mesolve(H, psi0, times, sc_ops, e_ops, args={"w": 2})

    options = {
        "map": "serial",
    }

    res = ssesolve(
        H, psi0, times, sc_ops, e_ops,
        ntraj=ntraj, args={"w": 2}, options=options, heterodyne=heterodyne,
        seeds=list(range(ntraj)),
    )

    for idx in range(len(e_ops)):
        np.testing.assert_allclose(
            res.expect[idx], res_ref.expect[idx], rtol=tol, atol=tol
        )

    assert res.measurement is None
    assert res.wiener_process is None
    assert res.dW is None


@pytest.mark.parametrize("heterodyne", [True, False])
@pytest.mark.parametrize("method", SSESolver.avail_integrators().keys())
def test_ssesolve_method(method, heterodyne):
    "Stochastic: smesolve: homodyne, time-dependent H"
    tol = 0.1
    N = 4
    ntraj = 20
    system = "simple"

    H, sc_ops = _make_system(N, system)
    psi0 = coherent(N, 0.5)
    a = destroy(N)
    e_ops = [a.dag() * a, a + a.dag(), (-1j)*(a - a.dag())]

    times = np.linspace(0, 0.1, 21)
    res_ref = mesolve(H, psi0, times, sc_ops, e_ops, args={"w": 2})

    options = {
        "store_measurement": True,
        "map": "serial",
        "method": method,
        "keep_runs_results": True,
    }

    res = ssesolve(
        H, psi0, times, sc_ops, e_ops,
        ntraj=ntraj, args={"w": 2}, options=options, heterodyne=heterodyne,
        seeds=1,
    )

    for idx in range(len(e_ops)):
        np.testing.assert_allclose(
            res.average_expect[idx], res_ref.expect[idx], rtol=tol, atol=tol
        )

    assert len(res.measurement) == ntraj

    if heterodyne:
        assert all([
            dw.shape == (len(sc_ops), 2, len(times)-1)
            for dw in res.dW
        ])
        assert all([
            w.shape == (len(sc_ops), 2, len(times))
            for w in res.wiener_process
        ])
        assert all([
            m.shape == (len(sc_ops), 2, len(times)-1)
            for m in res.measurement
        ])
    else:
        assert all([
            dw.shape == (len(sc_ops), len(times)-1)
            for dw in res.dW
        ])
        assert all([
            w.shape == (len(sc_ops), len(times))
            for w in res.wiener_process
        ])
        assert all([
            m.shape == (len(sc_ops), len(times)-1)
            for m in res.measurement
        ])


def test_reuse_seeds():
    "Stochastic: smesolve: homodyne, time-dependent H"
    tol = 0.05
    N = 4
    ntraj = 5

    H, sc_ops = _make_system(N, "simple")
    c_ops = [destroy(N)]
    psi0 = coherent(N, 0.5)
    a = destroy(N)
    e_ops = [a.dag() * a, a + a.dag(), (-1j)*(a - a.dag())]

    times = np.linspace(0, 0.1, 2)

    options = {
        "store_final_state": True,
        "map": "serial",
        "keep_runs_results": True,
    }

    res = smesolve(
        H, psi0, times, sc_ops=sc_ops, e_ops=e_ops, c_ops=c_ops,
        ntraj=ntraj, args={"w": 2}, options=options,
    )

    res2 = smesolve(
        H, psi0, times, sc_ops=sc_ops, e_ops=e_ops, c_ops=c_ops,
        ntraj=ntraj, args={"w": 2}, options=options,
        seeds=res.seeds,
    )

    for out1, out2 in zip(res.final_state, res2.final_state):
        assert out1 == out2

    np.testing.assert_allclose(res.expect, res2.expect, atol=1e-14)
