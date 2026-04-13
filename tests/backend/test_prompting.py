from app.models.schemas import RetrievedChunk
from app.services.prompting import PromptBuilder


def test_prompt_builder_adds_intro_guidance_for_broad_persona_question():
    builder = PromptBuilder(allow_general_tech_answers=True)

    prompt = builder.build(
        query="Tell me about yourself",
        retrieved_chunks=[
            RetrievedChunk(
                id="resume::0",
                source_id="resume",
                source_title="Ashwin Resume",
                source_type="resume",
                text="Ashwin resume summary.",
                score=0.91,
            )
        ],
        persona_question=True,
    )

    assert "Treat this as a self-introduction" in prompt.user_content
    assert "Do not jump straight into one project" in prompt.user_content
    assert "third-year Computer Science student in Bengaluru" in prompt.user_content


def test_prompt_builder_mentions_both_contribution_tracks_when_present():
    builder = PromptBuilder(allow_general_tech_answers=True)

    prompt = builder.build(
        query="What are your open source contributions? Tell in 2 lines.",
        retrieved_chunks=[
            RetrievedChunk(
                id="deepchem::0",
                source_id="deepchem",
                source_title="DeepChem Contributions",
                source_type="github",
                text="DeepChem contribution summary.",
                score=0.88,
            ),
            RetrievedChunk(
                id="gemini::0",
                source_id="gemini",
                source_title="Gemini CLI Contributions",
                source_type="github",
                text="Gemini CLI contribution summary.",
                score=0.86,
            ),
        ],
        persona_question=True,
    )

    assert "Mention both DeepChem and Gemini CLI" in prompt.user_content
    assert "at most two short sentences" in prompt.user_content


def test_prompt_builder_pushes_broad_project_questions_toward_multiple_projects():
    builder = PromptBuilder(allow_general_tech_answers=True)

    prompt = builder.build(
        query="What projects have you made?",
        retrieved_chunks=[
            RetrievedChunk(
                id="kv::0",
                source_id="kv",
                source_title="AshwinSaklecha/kv-cache",
                source_type="github",
                text="KV-Cache summary.",
                score=0.91,
            ),
            RetrievedChunk(
                id="expense::0",
                source_id="expense",
                source_title="AshwinSaklecha/expenseTracker",
                source_type="github",
                text="Expense Tracker summary.",
                score=0.88,
            ),
        ],
        persona_question=True,
    )

    assert "mention more than one relevant project" in prompt.user_content
    assert "Focus on personal projects first" in prompt.user_content
