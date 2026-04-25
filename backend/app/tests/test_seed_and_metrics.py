from app.services.demo_seed import seed_demo
from app.services.metrics import mtd_splits


async def _seed(session):
    return await seed_demo(session)


def test_seed_demo_creates_metrics(session):
    import asyncio

    counts = asyncio.run(_seed(session))
    assert counts["receipts"] == 2
    calories, spend = mtd_splits(session)
    assert calories.outside_schijf > 0
    assert spend.outside_schijf > 0

