"""Evidence labels are translated for display only; English labels and unknown labels pass through."""
from rely_brain.evidence_i18n import localise_label


def test_channel_share_window_and_substitution_labels_translate():
    assert localise_label("Right-channel share of progressive actions after", "tr") == "Sağ kanal: ileri aksiyon payı (sonra)"
    assert localise_label("Right-channel share of progressive actions before", "es") == "Carril derecho: cuota de acciones progresivas (antes)"
    assert localise_label("Before 46:03-56:03 vs after 56:03-60:09 (after window still open)", "tr") == (
        "Önce 46:03-56:03 · sonra 56:03-60:09 (sonrası penceresi hâlâ açık)")
    assert localise_label("Substitution 56:03: Kai Okafor on for Dario Mends", "es") == "Cambio 56:03: entra Kai Okafor, sale Dario Mends"
    assert localise_label("Shots after", "tr") == "Şut (sonra)"


def test_english_and_unknown_labels_are_unchanged():
    assert localise_label("Shots after", "en") == "Shots after"
    assert localise_label("Something new", "tr") == "Something new"
