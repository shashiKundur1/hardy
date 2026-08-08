from src.auth.avatar import markup, traits


def test_the_same_seed_always_draws_the_same_mark():
    assert markup("hardy:1:a@hardy.test", "A") == markup("hardy:1:a@hardy.test", "A")


def test_different_people_get_different_marks():
    drawn = {markup(f"hardy:{index}:person{index}@hardy.test", "x") for index in range(200)}
    assert len(drawn) > 150


def test_separation_survives_losing_colour_entirely():
    shapes = {
        tuple(
            traits(f"hardy:{index}:person{index}@hardy.test")[key]
            for key in ("spokes", "rings", "rivets", "form")
        )
        for index in range(200)
    }
    assert len(shapes) > 60


def test_the_mark_carries_the_name_for_assistive_technology():
    drawn = markup("hardy:1:a@hardy.test", "Ada Lovelace")
    assert 'role="img"' in drawn
    assert 'aria-label="Ada Lovelace"' in drawn
    assert "<title>Ada Lovelace</title>" in drawn


def test_a_name_cannot_inject_markup():
    drawn = markup("hardy:1:a@hardy.test", '"><script>alert(1)</script>')
    assert "<script>" not in drawn


def test_the_mark_draws_only_from_tokens():
    drawn = markup("hardy:1:a@hardy.test", "A")
    for swatch in ("#", "rgb(", "hsl("):
        assert swatch not in drawn
