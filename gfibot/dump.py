import json

from gfibot.collections import *

if __name__ == "__main__":
    dataset: List[Dataset] = Dataset.objects(owner="pandas-dev", name="pandas")
    result = []
    for item in dataset:
        if item.closed_at is None or item.before != item.closed_at:
            continue
        print(item.number, len(result))
        query = Q(name=item.name, owner=item.owner, number=item.number)
        issue: RepoIssue = RepoIssue.objects(query).first()
        resolved: ResolvedIssue = ResolvedIssue.objects(query).first()
        result.append(
            {
                "owner": item.owner,
                "name": item.name,
                "number": item.number,
                "reporter": issue.user,
                "created_at": item.created_at.isoformat(),
                "closed_at": item.closed_at.isoformat(),
                "resolver": resolved.resolver,
                "resolved_in": resolved.resolved_in,
                "resolver_commit_num": item.resolver_commit_num,
                "title": item.title,
                "body": item.body,
                "labels": item.labels,
                "comments": item.comments,
                "events": item.events,
            }
        )
    with open("pandas.json", "w") as f:
        json.dump(result, f, indent=2)
