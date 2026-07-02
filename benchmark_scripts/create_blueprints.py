#!/usr/bin/env python3
"""Create blueprint JSONs for episodes case_002 through case_010.

This script writes blueprint.json files for all 10 benchmark episodes
so the pipeline has valid input for every case. It does NOT run the pipeline.
"""

from __future__ import annotations
import json
from pathlib import Path

PROJECTS_DIR = Path(__file__).parent.parent / "projects"

EPISODES = [
    {
        "episode_id": "case_002",
        "title": "The Dead Letter Office",
        "logline": "A postal inspector discovers classified letters arriving with postmarks from before the sender died — and the return addresses belong to people who never existed.",
        "protagonist": {
            "name": "Marcus Cole",
            "role": "Senior Postal Inspector, USPS Office of Investigations",
            "flaw": "Obsessive attention to detail that blinds him to the bigger picture. Believes every anomaly has a rational explanation.",
        },
        "antagonist_system": "The Dead Letter Office — a covert communication network routing intelligence through undeliverable mail infrastructure.",
        "central_mystery": "Who is sending letters from the dead, and what are they trying to communicate?",
        "larger_mystery": "How deep does the mail-based covert network go? Who built it and who controls the dead drops?",
        "themes": ["perception_vs_reality", "hidden_systems", "surveillance_state"],
        "tone": "Forensic, atmospheric, methodical. The banality of bureaucratic evil.",
        "estimated_duration_seconds": 540,
        "total_scenes": 5,
        "inspirations": ["The Conversation", "Tinker Tailor Soldier Spy", "The Wire"],
    },
    {
        "episode_id": "case_003",
        "title": "The Sleepers Protocol",
        "logline": "A neurologist treating 47 coma patients across 12 cities discovers they all share the same impossible recurring dream — and someone is trying to wake them up.",
        "protagonist": {
            "name": "Dr. Aisha Sharma",
            "role": "Neurologist, Johns Hopkins Coma Recovery Unit",
            "flaw": "Empathy without boundaries. She cares too deeply and loses objectivity in pursuit of saving her patients.",
        },
        "antagonist_system": "The Sleepers Protocol — a neural-interface program using comatose subjects as organic data processors.",
        "central_mystery": "Why are 47 unrelated coma patients sharing the same dream, and who is sending the signal?",
        "larger_mystery": "What is the Sleepers Protocol processing, and who commissioned it?",
        "themes": ["perception_vs_reality", "hidden_systems", "identity_collapse"],
        "tone": "Clinical, haunting, intimate. The horror of minds trapped in bodies.",
        "estimated_duration_seconds": 660,
        "total_scenes": 6,
        "inspirations": ["Awakenings", "The Cell", "Black Mirror: Men Against Fire"],
    },
    {
        "episode_id": "case_004",
        "title": "The Carbon Copy",
        "logline": "A forensic accountant uncovers five competing companies with identical off-book ledgers — all handwritten by the same dead accountant who died in a car crash 10 years ago.",
        "protagonist": {
            "name": "David Park",
            "role": "Forensic Accountant, Financial Crimes Unit",
            "flaw": "Believes numbers never lie. He trusts spreadsheets more than people, making him blind to human corruption.",
        },
        "antagonist_system": "The Carbon Copy Network — a money-laundering syndicate using ghost companies and dead identities to move untraceable capital.",
        "central_mystery": "Who forged the ledgers, and whose money is being laundered through these phantom companies?",
        "larger_mystery": "What is the money funding? An operation larger than any single government agency.",
        "themes": ["hidden_systems", "surveillance_state", "moral_ambiguity"],
        "tone": "Clinical, paranoid, urgent. The banality of financial evil.",
        "estimated_duration_seconds": 600,
        "total_scenes": 5,
        "inspirations": ["The Big Short", "Ozark", "The Laundromat"],
    },
    {
        "episode_id": "case_005",
        "title": "The Hollow Men",
        "logline": "A priest discovers his church's AI confession-analysis system is flagging sins that haven't been committed yet — and the predictions are coming true.",
        "protagonist": {
            "name": "Father Gabriel Torres",
            "role": "Parish Priest, St. Dominic's Church",
            "flaw": "Faith in redemption. He believes everyone can be saved — even when the evidence says otherwise.",
        },
        "antagonist_system": "Project Halo — a behavioral prediction program co-opting church confession infrastructure for pre-crime surveillance.",
        "central_mystery": "How is the system predicting future sins with perfect accuracy, and who is feeding it data?",
        "larger_mystery": "Is the system predicting the future, or causing it?",
        "themes": ["perception_vs_reality", "surveillance_state", "moral_ambiguity", "the_system_survives"],
        "tone": "Atmospheric, theological, tense. Grace and paranoia in equal measure.",
        "estimated_duration_seconds": 720,
        "total_scenes": 6,
        "inspirations": ["Spotlight", "Minority Report", "The Exorcist"],
    },
    {
        "episode_id": "case_006",
        "title": "The Vanishing Point",
        "logline": "An archivist at the National Photo Archive notices historical photographs subtly changing — buildings appearing, people disappearing — and realizes someone is editing the past in real-time.",
        "protagonist": {
            "name": "Nina Okafor",
            "role": "Senior Archivist, National Historical Photo Archive",
            "flaw": "Clings to evidence of the past as immutable truth. The idea that history can be rewritten paralyzes her.",
        },
        "antagonist_system": "The Revision Desk — a media manipulation program using AI to retroactively alter visual historical records.",
        "central_mystery": "Who is changing the photographs, and what version of history are they trying to create?",
        "larger_mystery": "How far back does the revision go? Are digital files the only things being altered?",
        "themes": ["perception_vs_reality", "identity_collapse", "hidden_systems"],
        "tone": "Meditative, unsettling, lyrical. The fragility of recorded truth.",
        "estimated_duration_seconds": 540,
        "total_scenes": 5,
        "inspirations": ["The Report", "Blow-Up", "Zola's La Bête Humaine"],
    },
    {
        "episode_id": "case_007",
        "title": "The Echo Chamber",
        "logline": "An acoustic engineer discovers inaudible messages hidden in the background noise of every government building in the capital — a ghost network speaking to no one.",
        "protagonist": {
            "name": "Leo Chen",
            "role": "Acoustic Engineer, National Audio Forensics Lab",
            "flaw": "Hears patterns where none exist. His greatest strength is also his blind spot — he finds meaning in noise.",
        },
        "antagonist_system": "The Echo Chamber — a audio steganography network embedding commands in ambient environmental noise across government facilities.",
        "central_mystery": "Who embedded the messages, who is supposed to hear them, and what do they say?",
        "larger_mystery": "What happens when the messages are activated? What action do they trigger?",
        "themes": ["hidden_systems", "surveillance_state", "perception_vs_reality", "the_system_survives"],
        "tone": "Technical, paranoid, immersive. The paranoia of hearing what others cannot.",
        "estimated_duration_seconds": 600,
        "total_scenes": 5,
        "inspirations": ["Blow Out", "The Conversation", "Enemy of the State"],
    },
    {
        "episode_id": "case_008",
        "title": "The Fence",
        "logline": "A border patrol analyst discovers the biometric database shows 2 million more crossings than any human agent recorded — and the phantom entries are all using the same face.",
        "protagonist": {
            "name": "Sarah Kessler",
            "role": "Data Analyst, Border Security Biometrics Division",
            "flaw": "Rigid adherence to protocol. She trusts the system's rules more than her own instincts.",
        },
        "antagonist_system": "The Fence — a synthetic identity pipeline injecting fabricated border crossings to legitimize phantom citizens.",
        "central_mystery": "Who is the face in the phantom crossings, and whose identities are being manufactured?",
        "larger_mystery": "What are the phantom citizens being positioned to do? An infiltration campaign of unprecedented scale.",
        "themes": ["identity_collapse", "surveillance_state", "hidden_systems", "moral_ambiguity"],
        "tone": "Urgent, clinical, claustrophobic. The border as a sieve, not a wall.",
        "estimated_duration_seconds": 660,
        "total_scenes": 6,
        "inspirations": ["Sicario", "The Bureau", "Traffic"],
    },
    {
        "episode_id": "case_009",
        "title": "The Zero Day",
        "logline": "A high school teacher discovers his 16-year-old student predicted a catastrophic natural disaster with 100% accuracy using only public data — and now someone is trying very hard to make the student disappear.",
        "protagonist": {
            "name": "Jamal Brooks",
            "role": "AP Computer Science Teacher, Westbrook High School",
            "flaw": "Protective to a fault. He sees his students as his children and will cross any line to keep them safe.",
        },
        "antagonist_system": "The Prospect Program — a talent-scouting operation that identifies and recruits predictive individuals before their abilities become public.",
        "central_mystery": "How did the student make the prediction, and what else has she predicted that someone wants hidden?",
        "larger_mystery": "How many other prodigies have been recruited? What is the Prospect Program building toward?",
        "themes": ["hidden_systems", "moral_ambiguity", "the_system_survives"],
        "tone": "Intimate, urgent, suspenseful. The race to protect a child from a system that wants to use her.",
        "estimated_duration_seconds": 720,
        "total_scenes": 6,
        "inspirations": ["Searching for Bobby Fischer", "The Recruit", "Good Will Hunting"],
    },
    {
        "episode_id": "case_010",
        "title": "The Long Game",
        "logline": "A historian discovers that 200-year-old Masonic lodge records contain coded entries that precisely predict every major stock market crash — and the next prediction is tomorrow.",
        "protagonist": {
            "name": "Dr. Helena Ross",
            "role": "Professor of Historical Cryptography, Oxford University",
            "flaw": "Academic detachment. She believes she can observe the darkness without being consumed by it.",
        },
        "antagonist_system": "The Long Game — a centuries-old trans-generational cabal using coded historical records to coordinate economic manipulation across generations.",
        "central_mystery": "Who wrote the predictions, and how could they possibly be accurate 200 years later?",
        "larger_mystery": "What is the Long Game's endgame? A final event the cabal has been orchestrating for centuries.",
        "themes": ["hidden_systems", "perception_vs_reality", "the_system_survives"],
        "tone": "Epic, philosophical, methodical. The weight of centuries of hidden orchestration.",
        "estimated_duration_seconds": 840,
        "total_scenes": 7,
        "inspirations": ["The Da Vinci Code", "National Treasure", "The Order"],
    },
]


def main() -> None:
    for ep in EPISODES:
        case_dir = PROJECTS_DIR / ep["episode_id"]
        case_dir.mkdir(parents=True, exist_ok=True)
        blueprint_path = case_dir / "blueprint.json"
        if blueprint_path.exists():
            print(f"  EXISTS: {ep['episode_id']}/blueprint.json (skipping)")
        else:
            blueprint_path.write_text(json.dumps(ep, indent=2) + "\n")
            print(f"  CREATED: {ep['episode_id']}/blueprint.json")
    print(f"\nDone. {len(EPISODES)} blueprints ready.")


if __name__ == "__main__":
    main()
