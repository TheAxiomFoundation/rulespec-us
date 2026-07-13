import pytest

from bulk.compute_matrix import APPROVED_ENCODER_REFS, select

APPROVED_ENCODER_REF = next(iter(APPROVED_ENCODER_REFS))


def test_select_carries_entry_encoder_ref_into_matrix() -> None:
    data = {
        "defaults": {
            "backend": "openai",
            "model": "gpt-5.5",
                "encoder_ref": APPROVED_ENCODER_REF,
        },
        "entries": [
            {
                "citation": "us-mo/manual/dss/snap/1105/block-1",
                "repo": "rulespec-us",
                "batch": "SNAP-MO-1",
                "status": "pending",
                "encoder_ref": APPROVED_ENCODER_REF,
            },
            {
                "citation": "us-il/statute/35/5/402",
                "status": "pending",
            },
        ],
    }

    selected = select(data, "pending", "snap-mo-1", 1)

    assert selected == [
        {
            "citation": "us-mo/manual/dss/snap/1105/block-1",
            "repo": "rulespec-us",
            "backend": "openai",
            "model": "gpt-5.5",
            "encoder_ref": APPROVED_ENCODER_REF,
            "slug": "us-mo-manual-dss-snap-1105-block-1",
        }
    ]


def test_select_uses_default_encoder_ref() -> None:
    data = {
        "defaults": {"encoder_ref": APPROVED_ENCODER_REF},
        "entries": [
            {
                "citation": "us-il/statute/35/5/402",
                "status": "pending",
            }
        ],
    }

    assert select(data, "pending", None, None)[0]["encoder_ref"] == APPROVED_ENCODER_REF


def test_select_rejects_mutable_encoder_ref() -> None:
    data = {
        "entries": [
            {
                "citation": "us-mo/manual/dss/snap/1105/block-1",
                "status": "pending",
                "encoder_ref": "compat/manual-signing",
            }
        ]
    }

    with pytest.raises(ValueError, match="full 40-character lowercase commit SHA"):
        select(data, "pending", None, None)


def test_select_without_override_keeps_toolchain_fallback() -> None:
    data = {
        "entries": [
            {
                "citation": "us-il/statute/35/5/402",
                "status": "pending",
            }
        ]
    }

    assert select(data, "pending", None, None)[0]["encoder_ref"] == ""


def test_select_rejects_unapproved_immutable_encoder_ref() -> None:
    data = {
        "entries": [
            {
                "citation": "us-mo/manual/dss/snap/1105/block-1",
                "status": "pending",
                "encoder_ref": "f" * 40,
            }
        ]
    }

    with pytest.raises(ValueError, match="reviewed compatibility allowlist"):
        select(data, "pending", None, None)
