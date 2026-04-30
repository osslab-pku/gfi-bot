def count_by_month(dates: List[datetime]) -> List[Repo.MonthCount]:
    counts = Counter(map(lambda d: (d.year, d.month), dates))
    return sorted(
        [
            Repo.MonthCount(
                month=datetime(year=y, month=m, day=1, tzinfo=timezone.utc), count=c
            )
            for (y, m), c in counts.items()
        ],
        key=lambda k: k["month"],
    )
