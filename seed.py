"""
Demo seed script — populates a pre-baked session so you never rely on
live AI generation during the judging round.

Usage:
    poetry run python seed.py

Re-run safely by truncating tables in Supabase dashboard first, then re-run.
"""

import uuid
import json
from app.db import SessionLocal
from app.models.session import Session
from app.models.participant import Participant
from app.models.question import Question, QuestionOption
from app.models.answer import Answer
from app.models.swipe import CategoryOption, Swipe
from app.constants import SessionState, Mechanic, SwipeDirection

db = SessionLocal()


def seed_demo():
    print("Seeding demo session...")

    # --- Session ---
    session = Session(
        id=uuid.uuid4(),
        topic="Saturday hangout",
        context="6 friends, mix of introverts and extroverts, some have cars",
        state=SessionState.QUESTION_PHASE,
        expected_count=6,
        answered_count=0,
    )
    db.add(session)
    db.flush()

    # --- Participants ---
    names = [
        "CouchPotato99",
        "AlwaysLate_Dan",
        "VetoQueen",
        "BudgetHawk",
        "SpontaneousSam",
        "NightOwlNadia",
    ]
    participants = []
    for name in names:
        p = Participant(session_id=session.id, display_name=name)
        db.add(p)
        participants.append(p)
    db.flush()

    session.host_id = participants[0].id

    # --- Questions ---
    q1 = Question(session_id=session.id, text="Indoor or outdoor?",
                  mechanic=Mechanic.SWIPE, display_order=1)
    q2 = Question(session_id=session.id, text="When works for you?",
                  mechanic=Mechanic.MULTISELECT, display_order=2)
    q3 = Question(session_id=session.id, text="😴 chill vibes → 🔥 high energy",
                  mechanic=Mechanic.SLIDER, display_order=3)
    q4 = Question(session_id=session.id, text="Budget per person? ($)",
                  mechanic=Mechanic.SLIDER, display_order=4)
    q5 = Question(session_id=session.id, text="Any dietary or access needs?",
                  mechanic=Mechanic.TEXT, display_order=5)

    for q in [q1, q2, q3, q4, q5]:
        db.add(q)
    db.flush()

    for label in ["Saturday morning", "Saturday afternoon", "Saturday evening",
                  "Sunday morning", "Other / Any"]:
        db.add(QuestionOption(question_id=q2.id, label=label))
    db.flush()

    # --- Answers (one set per participant) ---
    # Format: (q1-swipe, q2-multiselect, q3-energy-slider, q4-budget-slider, q5-text)
    answer_sets = [
        ("YES", ["Saturday morning", "Saturday afternoon"], 30, 35, "vegetarian"),
        ("YES", ["Saturday morning"], 25, 25, "none"),
        ("YES", ["Saturday afternoon", "Saturday evening"], 60, 50, "none"),
        ("NO",  ["Saturday morning", "Sunday morning"], 20, 20, "peanut allergy"),
        ("YES", ["Saturday morning"], 45, 40, "none"),
        ("YES", ["Saturday morning", "Saturday afternoon"], 35, 30, "no car"),
    ]

    for p, (swipe, multiselect, energy, budget, text) in zip(participants, answer_sets):
        db.add(Answer(participant_id=p.id, question_id=q1.id, value=swipe))
        db.add(Answer(participant_id=p.id, question_id=q2.id, value=json.dumps(multiselect)))
        db.add(Answer(participant_id=p.id, question_id=q3.id, value=json.dumps({"value": energy})))
        db.add(Answer(participant_id=p.id, question_id=q4.id, value=json.dumps({"value": budget})))
        db.add(Answer(participant_id=p.id, question_id=q5.id, value=text))

    session.answered_count = 6
    session.state = SessionState.REVEAL

    # --- Category options (pre-baked; no AI call needed during demo) ---
    categories = [
        (
            "Farmers Market",
            "Fits Saturday morning (6/6 available), outdoor-friendly, free entry — "
            "within everyone's $20–$50 budget for food",
        ),
        (
            "Brunch Spot",
            "Accommodates the vegetarian and peanut allergy, indoor preference of 5/6, "
            "Saturday morning works for all 6",
        ),
        (
            "Board Game Café",
            "Indoor (preferred by 5/6), low-energy vibe (average energy score 36/100), "
            "$15–$25 per person fits all budgets",
        ),
        (
            "Morning Hike",
            "Saturday morning works for everyone, high overlap with outdoor preference, "
            "free — well under all budgets. Note: 1 person has no car, needs a ride",
        ),
        (
            "Cooking Class",
            "Indoor, fits budget range $30–$50, accommodates vegetarian, "
            "accessible without a car",
        ),
    ]

    cat_objects = []
    for name, reasoning in categories:
        c = CategoryOption(session_id=session.id, name=name, reasoning=reasoning)
        db.add(c)
        cat_objects.append(c)
    db.flush()

    # --- Swipes (tuned to produce a clear Brunch Spot consensus) ---
    swipe_votes = [
        # Farmers  Brunch  BoardGame  Hike  Cooking
        ["YES",   "YES",  "NO",      "YES", "NO"],   # CouchPotato99
        ["YES",   "YES",  "NO",      "YES", "YES"],  # AlwaysLate_Dan
        ["NO",    "YES",  "YES",     "NO",  "YES"],  # VetoQueen
        ["YES",   "YES",  "YES",     "NO",  "NO"],   # BudgetHawk
        ["YES",   "NO",   "NO",      "YES", "YES"],  # SpontaneousSam
        ["YES",   "YES",  "NO",      "NO",  "YES"],  # NightOwlNadia
    ]

    for p, votes in zip(participants, swipe_votes):
        for cat, vote in zip(cat_objects, votes):
            db.add(Swipe(
                participant_id=p.id,
                category_id=cat.id,
                direction=SwipeDirection.YES if vote == "YES" else SwipeDirection.NO,
            ))

    session.state = SessionState.RESULTS
    db.commit()

    print(f"✅ Demo session created: {session.id}")
    print(f"   Share link: /sessions/{session.id}/join")
    print(f"   Participants: {', '.join(names)}")
    print(f"   State: {session.state}")


if __name__ == "__main__":
    seed_demo()
    db.close()
