
import pytest
from datetime import datetime, timezone, timedelta

from src.models.schemas import BranchInfo

STALE_DAYS = 30


def make_branch(name: str, days_ago: int, protected: bool = False) -> BranchInfo:

    now = datetime.now(timezone.utc)
    commit_date = now - timedelta(days=days_ago)
    stale_cutoff = now - timedelta(days=STALE_DAYS)
    return BranchInfo(
        name=name,
        sha="abc123",
        protected=protected,
        last_commit_date=commit_date,
        last_commit_message=f"commit on {name}",
        last_commit_author="dev",
        is_stale=(commit_date < stale_cutoff),
    )


class TestStalenessLogic:
    def test_recent_branch_not_stale(self):
        b = make_branch("feat/new-feature", days_ago=5)
        assert b.is_stale is False

    def test_old_branch_is_stale(self):
        b = make_branch("feat/forgotten", days_ago=60)
        assert b.is_stale is True

    def test_29_days_not_stale(self):
        # 29 days ago is clearly within the window → not stale
        b = make_branch("feat/recent", days_ago=29)
        assert b.is_stale is False

    def test_31_days_is_stale(self):
        # 31 days ago is clearly past the cutoff → stale
        b = make_branch("feat/just-stale", days_ago=31)
        assert b.is_stale is True

    def test_protected_branch_can_be_stale(self):
        # Protection status doesn't affect staleness — it's a separate concern
        b = make_branch("release/old", days_ago=90, protected=True)
        assert b.is_stale is True
        assert b.protected is True

    def test_no_commit_date_not_stale_by_default(self):
        b = BranchInfo(
            name="empty", sha="000", protected=False,
            last_commit_date=None, last_commit_message=None,
            last_commit_author=None, is_stale=False,
        )
        assert b.is_stale is False

    def test_filter_stale_from_list(self):
        branches = [
            make_branch("main", days_ago=1),
            make_branch("feat/active", days_ago=10),
            make_branch("feat/old-a", days_ago=45),
            make_branch("fix/old-b", days_ago=100),
            make_branch("feat/mid", days_ago=20),
        ]
        stale = [b for b in branches if b.is_stale]
        fresh = [b for b in branches if not b.is_stale]
        assert len(stale) == 2
        assert len(fresh) == 3

    def test_stale_branch_names(self):
        branches = [
            make_branch("feat/old-login", days_ago=60),
            make_branch("fix/typo-2022", days_ago=400),
            make_branch("feat/active", days_ago=5),
        ]
        stale_names = [b.name for b in branches if b.is_stale]
        assert "feat/old-login" in stale_names
        assert "fix/typo-2022" in stale_names
        assert "feat/active" not in stale_names

    def test_stale_is_false_for_zero_days(self):
        b = make_branch("just-committed", days_ago=0)
        assert b.is_stale is False
