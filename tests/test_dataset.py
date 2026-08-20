from institutional_investment_agents.dataset import DATASET_VERSION, generate_universe


def test_generator_is_reproducible() -> None:
    assert generate_universe(17) == generate_universe(17)


def test_seed_changes_market_values() -> None:
    assert (
        generate_universe(17).issuer("NRT").spread_bps
        != generate_universe(23).issuer("NRT").spread_bps
    )


def test_universe_has_unique_ids_and_sectors() -> None:
    universe = generate_universe()
    assert universe.version == DATASET_VERSION
    assert len(universe.issuers) == 10
    assert len({issuer.issuer_id for issuer in universe.issuers}) == 10
    assert len({issuer.sector for issuer in universe.issuers}) >= 6
    assert len({document.id for document in universe.documents}) == len(universe.documents)


def test_accounting_and_market_consistency() -> None:
    for issuer in generate_universe().issuers:
        assert abs(issuer.leverage - issuer.debt_bn / issuer.ebitda_bn) < 0.001
        assert abs((issuer.bond_yield - issuer.benchmark_yield) * 10_000 - issuer.spread_bps) < 0.11
        assert issuer.cash_bn < issuer.debt_bn or issuer.issuer_id == "VTX"
        assert issuer.true_risks


def test_unknown_issuer_fails() -> None:
    try:
        generate_universe().issuer("NOPE")
    except KeyError as error:
        assert "unknown issuer" in str(error)
    else:
        raise AssertionError("missing issuer should fail")
