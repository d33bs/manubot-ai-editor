from pathlib import Path
from unittest import mock

from manubot_ai_editor.editor import ManuscriptEditor
from manubot_ai_editor.models import GPT3CompletionModel, RandomManuscriptRevisionModel
from manubot_ai_editor.prompt_config import IGNORE_FILE
import pytest

from utils.dir_union import mock_unify_open

MANUSCRIPTS_DIR = Path(__file__).parent / "manuscripts" / "phenoplier_full"


# check that this path exists and resolve it
def test_manuscripts_dir_exists():
    content_dir = MANUSCRIPTS_DIR.resolve(strict=True)
    assert content_dir.exists()


# check that we can create a ManuscriptEditor object
def test_create_manuscript_editor():
    content_dir = MANUSCRIPTS_DIR.resolve(strict=True)
    editor = ManuscriptEditor(content_dir)
    assert isinstance(editor, ManuscriptEditor)


# ==============================================================================
# === prompts tests, using ai_revision-config.yaml + ai_revision-prompts.yaml
# ==============================================================================

# contains standard prompt, config files for phenoplier_full
# (this is merged into the manuscript folder using the mock_unify_open mock)
PHENOPLIER_PROMPTS_DIR = (
    Path(__file__).parent / "config_loader_fixtures" / "phenoplier_full"
)


# check that we can resolve a file to a prompt, and that it's the correct prompt
@mock.patch("builtins.open", mock_unify_open(MANUSCRIPTS_DIR, PHENOPLIER_PROMPTS_DIR))
def test_resolve_prompt():
    content_dir = MANUSCRIPTS_DIR.resolve(strict=True)
    editor = ManuscriptEditor(content_dir)

    phenoplier_files_matches = {
        # explicitly ignored in ai_revision-config.yaml
        "00.front-matter.md": (IGNORE_FILE, "front-matter"),
        # prompts that match a part of the filename
        "01.abstract.md": ("Test match abstract.\n", "abstract"),
        "02.introduction.md": (
            "Test match introduction or discussion.\n",
            "introduction",
        ),
        # these all match the regex 04\..+\.md, hence why the match object includes a suffix
        "04.00.results.md": ("Test match results.\n", "04.00.results.md"),
        "04.05.00.results_framework.md": (
            "Test match results.\n",
            "04.05.00.results_framework.md",
        ),
        "04.05.01.crispr.md": ("Test match results.\n", "04.05.01.crispr.md"),
        "04.15.drug_disease_prediction.md": (
            "Test match results.\n",
            "04.15.drug_disease_prediction.md",
        ),
        "04.20.00.traits_clustering.md": (
            "Test match results.\n",
            "04.20.00.traits_clustering.md",
        ),
        # more prompts that match a part of the filename
        "05.discussion.md": ("Test match introduction or discussion.\n", "discussion"),
        "07.00.methods.md": ("Test match methods.\n", "methods"),
        # these are all explicitly ignored in ai_revision-config.yaml
        "10.references.md": (IGNORE_FILE, "references"),
        "15.acknowledgements.md": (IGNORE_FILE, "acknowledgements"),
        "50.00.supplementary_material.md": (IGNORE_FILE, "supplementary_material"),
    }

    for filename, (expected_prompt, expected_match) in phenoplier_files_matches.items():
        prompt, match = editor.prompt_config.get_prompt_for_filename(filename)

        if expected_prompt is None:
            assert prompt is None
        else:
            # we strip() here so that tests still pass, even if the user uses
            # newlines to separate blocks and isn't aware that the trailing
            # newline becomes part of the value
            assert prompt.strip() == expected_prompt.strip()

        if expected_match is None:
            assert match is None
        else:
            assert match.string[match.start() : match.end()] == expected_match


# test that we get the default prompt with a None match object for a
# file we don't recognize
@mock.patch("builtins.open", mock_unify_open(MANUSCRIPTS_DIR, PHENOPLIER_PROMPTS_DIR))
def test_resolve_default_prompt_unknown_file():
    content_dir = MANUSCRIPTS_DIR.resolve(strict=True)
    editor = ManuscriptEditor(content_dir)

    prompt, match = editor.prompt_config.get_prompt_for_filename("some-unknown-file.md")

    assert prompt.strip() == """default prompt text"""
    assert match is None


# check that a file we don't recognize gets match==None and the 'default' prompt
# from the ai_revision-config.yaml file
@mock.patch("builtins.open", mock_unify_open(MANUSCRIPTS_DIR, PHENOPLIER_PROMPTS_DIR))
def test_unresolved_gets_default_prompt():
    content_dir = MANUSCRIPTS_DIR.resolve(strict=True)
    editor = ManuscriptEditor(content_dir)
    prompt, match = editor.prompt_config.get_prompt_for_filename("crazy-filename")

    assert isinstance(prompt, str)
    assert match is None

    assert prompt.strip() == """default prompt text"""


# ==============================================================================
# === prompts_files tests, using ai_revision-prompts.yaml w/ai_revision-config.yaml to process ignores, defaults
# ==============================================================================

# the following tests are derived from examples in
# https://github.com/manubot/manubot-ai-editor/issues/31
# we test four different scenarios from ./config_loader_fixtures:
# - Only ai_revision-prompts.yaml is defined (only_revision_prompts)
ONLY_REV_PROMPTS_DIR = (
    Path(__file__).parent / "config_loader_fixtures" / "only_revision_prompts"
)
# - Both ai_revision-prompts.yaml and ai_revision-config.yaml are defined (both_prompts_config)
BOTH_PROMPTS_CONFIG_DIR = (
    Path(__file__).parent / "config_loader_fixtures" / "both_prompts_config"
)
# - Only a single, generic prompt is defined (single_generic_prompt)
SINGLE_GENERIC_PROMPT_DIR = (
    Path(__file__).parent / "config_loader_fixtures" / "single_generic_prompt"
)
# - Both ai_revision-config.yaml and ai-revision-prompts.yaml specify filename matchings
#   (conflicting_promptsfiles_matchings)
CONFLICTING_PROMPTSFILES_MATCHINGS_DIR = (
    Path(__file__).parent / "config_loader_fixtures" / "conflicting_promptsfiles_matchings"
)
# ---
# test ManuscriptEditor.prompt_config sub-attributes are set correctly
# ---


def get_editor():
    content_dir = MANUSCRIPTS_DIR.resolve(strict=True)
    editor = ManuscriptEditor(content_dir)
    assert isinstance(editor, ManuscriptEditor)
    return editor


def test_no_config_unloaded():
    """
    With no config files defined, the ManuscriptPromptConfig object should
    have its attributes set to None.
    """
    editor = get_editor()

    # ensure that only the prompts defined in ai_revision-prompts.yaml are loaded
    assert editor.prompt_config.prompts is None
    assert editor.prompt_config.prompts_files is None
    assert editor.prompt_config.config is None


@mock.patch("builtins.open", mock_unify_open(MANUSCRIPTS_DIR, ONLY_REV_PROMPTS_DIR))
def test_only_rev_prompts_loaded():
    editor = get_editor()

    # ensure that only the prompts defined in ai_revision-prompts.yaml are loaded
    assert editor.prompt_config.prompts is None
    assert editor.prompt_config.prompts_files is not None
    assert editor.prompt_config.config is None


@mock.patch("builtins.open", mock_unify_open(MANUSCRIPTS_DIR, BOTH_PROMPTS_CONFIG_DIR))
def test_both_prompts_loaded():
    editor = get_editor()

    # ensure that only the prompts defined in ai_revision-prompts.yaml are loaded
    assert editor.prompt_config.prompts is not None
    assert editor.prompt_config.prompts_files is None
    assert editor.prompt_config.config is not None


@mock.patch(
    "builtins.open", mock_unify_open(MANUSCRIPTS_DIR, SINGLE_GENERIC_PROMPT_DIR)
)
def test_single_generic_loaded():
    editor = get_editor()

    # ensure that only the prompts defined in ai_revision-prompts.yaml are loaded
    assert editor.prompt_config.prompts is None
    assert editor.prompt_config.prompts_files is not None
    assert editor.prompt_config.config is not None


@mock.patch(
    "builtins.open", mock_unify_open(MANUSCRIPTS_DIR, CONFLICTING_PROMPTSFILES_MATCHINGS_DIR)
)
def test_conflicting_sources_warning(capfd):
    """
    Tests that a warning is printed when both ai_revision-prompts.yaml and
    ai_revision-config.yaml specify filename-to-prompt mappings.

    Specifically, the dicts that map filenames to prompts are:
    - ai_revision-prompts.yaml: 'prompts_files'
    - ai_revision-config.yaml: 'files.matchings'

    If both are specified, the 'files.matchings' key in ai_revision-config.yaml
    takes precedence, but a warning is printed.
    """

    editor = get_editor()

    # ensure that only the prompts defined in ai_revision-prompts.yaml are loaded
    assert editor.prompt_config.prompts is None
    assert editor.prompt_config.config is not None
    # for this test, we define both prompts_files and files.matchings which
    # creates a conflict that produces the warning we're looking for
    assert editor.prompt_config.prompts_files is not None
    assert editor.prompt_config.config['files']['matchings'] is not None

    expected_warning = (
        "WARNING: Both 'ai_revision-config.yaml' and "
        "'ai_revision-prompts.yaml' specify filename-to-prompt mappings. Only the "
        "'ai_revision-config.yaml' file's file.matchings section will be used; "
        "prompts_files will be ignored."
    )

    out, _ = capfd.readouterr()
    assert expected_warning in out

# ---
# test that ignored files are ignored in applicable scenarios
# ---

# places in configs where files can be ignored:
# ai_revision-config.yaml: the `files.ignore` key
# ai_revision-prompts.yaml: when a prompt in `prompts_files` has a value of null


@pytest.mark.parametrize(
    "model",
    [
        RandomManuscriptRevisionModel(),
        GPT3CompletionModel(None, None),
    ],
)
@mock.patch("builtins.open", mock_unify_open(MANUSCRIPTS_DIR, BOTH_PROMPTS_CONFIG_DIR))
def test_revise_entire_manuscript(tmp_path, model):
    print(f"\n{str(tmp_path)}\n")
    me = get_editor()

    model.title = me.title
    model.keywords = me.keywords

    output_folder = tmp_path
    assert output_folder.exists()

    me.revise_manuscript(output_folder, model)

    # after processing ignores, we should be left with 9 files from the original 12
    output_md_files = list(output_folder.glob("*.md"))
    assert len(output_md_files) == 9
