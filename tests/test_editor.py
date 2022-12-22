from pathlib import Path

from chatgpt_editor.editor import ManuscriptEditor
from chatgpt_editor.models import DummyManuscriptRevisionModel, GPT3CompletionModel

MANUSCRIPTS_DIR = Path(__file__).parent / "manuscripts"


def _check_nonparagraph_lines_are_preserved(input_filepath, output_filepath):
    """
    Checks whether non-paragraph lines in the input file are preserved in the output file.
    Non-paragraph lines are those that represent section headers, comments, blank lines, as
    defined in function ManuscriptEditor.line_is_not_part_of_paragraph.
    """
    # read lines from input file
    filepath = input_filepath
    assert filepath.exists()
    with open(filepath, "r") as infile:
        input_nonpar_lines = [
            line.rstrip()
            for line in infile
            if ManuscriptEditor.line_is_not_part_of_paragraph(line)
        ]

    # read lines from output file
    filepath = output_filepath
    assert filepath.exists()
    with open(filepath, "r") as infile:
        output_nonpar_lines = [
            line.rstrip()
            for line in infile
            if ManuscriptEditor.line_is_not_part_of_paragraph(line)
        ]

    # make sure all lines that are not "paragraphs" are preserved
    for input_line in input_nonpar_lines:
        # make sure there are nonparagraph lines left in output file
        assert (
            len(output_nonpar_lines) > 0
        ), "Output file has less non-paragraph lines than input file"

        # make sure nonparagraph lines are in the same order
        assert (
            input_line == output_nonpar_lines[0]
        ), f"{input_line} != {output_nonpar_lines[0]}"

        output_nonpar_lines.remove(input_line)

    # if nonparagraph lines were preserved, then the output_nonpar_liens should be empty
    assert (
        len(output_nonpar_lines) == 0
    ), f"Non-paragraph lines are not the same: {output_nonpar_lines}"


def test_revise_abstract(tmp_path):
    me = ManuscriptEditor(
        content_dir=MANUSCRIPTS_DIR / "ccc",
    )

    model = DummyManuscriptRevisionModel()

    me.revise_file("01.abstract.md", tmp_path, model)

    _check_nonparagraph_lines_are_preserved(
        input_filepath=MANUSCRIPTS_DIR / "ccc" / "01.abstract.md",
        output_filepath=tmp_path / "01.abstract.md",
    )


def test_revise_abstract_paragraph_lines_do_not_start_with_space(tmp_path):
    me = ManuscriptEditor(
        content_dir=MANUSCRIPTS_DIR / "ccc",
    )

    model = DummyManuscriptRevisionModel()

    me.revise_file("01.abstract.md", tmp_path, model)

    filepath = tmp_path / "01.abstract.md"
    assert filepath.exists()
    with open(filepath, "r") as infile:
        output_par_lines = [
            line.rstrip()
            for line in infile
            if not ManuscriptEditor.line_is_not_part_of_paragraph(line)
        ]

    assert all([not line.startswith(" ") for line in output_par_lines])


def test_revise_abstract_using_completion_model(tmp_path):
    me = ManuscriptEditor(
        content_dir=MANUSCRIPTS_DIR / "ccc",
    )

    model = GPT3CompletionModel(
        title=me.title,
        keywords=me.keywords,
    )

    me.revise_file("01.abstract.md", tmp_path, model)

    _check_nonparagraph_lines_are_preserved(
        input_filepath=MANUSCRIPTS_DIR / "ccc" / "01.abstract.md",
        output_filepath=tmp_path / "01.abstract.md",
    )


def test_revise_introduction(tmp_path):
    me = ManuscriptEditor(
        content_dir=MANUSCRIPTS_DIR / "ccc",
    )

    model = DummyManuscriptRevisionModel()

    me.revise_file("02.introduction.md", tmp_path, model)

    _check_nonparagraph_lines_are_preserved(
        input_filepath=MANUSCRIPTS_DIR / "ccc" / "02.introduction.md",
        output_filepath=tmp_path / "02.introduction.md",
    )
