from app.services.ai_model import ai_model


def test_predict_proba_range():
    p = ai_model.predict_proba("URGENT: Your account has been suspended! Verify your password now.")
    assert 0.0 <= p <= 1.0


def test_obvious_cases():
    assert ai_model.predict_proba("URGENT: your account is suspended, click here to verify your password") > 0.5
    assert ai_model.predict_proba("Hi team, attached are the minutes from the Tuesday project meeting.") < 0.5


def test_top_terms():
    terms = ai_model.top_terms("Verify your account password immediately or it will be suspended", k=5)
    assert 0 < len(terms) <= 5
    assert {"feature", "weight"} <= set(terms[0])
