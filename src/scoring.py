import csv
import pathlib
import typing as tp

import numpy as np

import data_exporting
import grid_info
import list_utils
import math_utils


def get_key_form_code(answer_keys: data_exporting.OutputSheet,
                      index: int) -> str:
    """Gets the form code of the answer key at the index given, where the first
    answer key has index=0."""
    keys = answer_keys.data
    form_code_column_name = data_exporting.COLUMN_NAMES[
        grid_info.Field.TEST_FORM_CODE]
    try:
        # Get the index of the column that had the test form codes
        form_code_index = list_utils.find_index(keys[0], form_code_column_name)
        return keys[index + 1][form_code_index]
    except StopIteration:
        return "*"


def establish_key_dict(answer_keys: data_exporting.OutputSheet
                       ) -> tp.Dict[str, tp.List[str]]:
    """Takes the matrix of answer keys and transforms it into a dictionary that
    maps the test form codes to the list of correct answers.

    Treats the answer_keys data naively by assuming the following:
        * The column with the form codes comes before the answer columns.
        * The first answer column is named "Q1".
        * The answers are all in order.
    If these are wrong, the results will be incorrect.

    Also note: the returned list of answers matches the order of the questions,
    but the questions are named "Q1" through "Q75" and the answers are in indexes
    0 through 74.
    """

    try:
        answers_start_index = list_utils.find_index(answer_keys.data[0], "Q1")
    except StopIteration:
        raise ValueError(
            "Invalid key matrix passed to scoring functions. Answers columns must be named 'Q1' through 'QN'."
        )
    key_scores = {
        get_key_form_code(answer_keys, index): list(zip(key[answers_start_index:], answer_keys.scores[index]))
        for index, key in enumerate(answer_keys.data[1:])
    }
    return key_scores


def score_results(results: data_exporting.OutputSheet,
                  answer_keys: data_exporting.OutputSheet,
                  num_questions: int) -> data_exporting.OutputSheet:
    answers = results.data
    keys_scores = establish_key_dict(answer_keys)
    form_code_column_name = data_exporting.COLUMN_NAMES[
        grid_info.Field.TEST_FORM_CODE]
    form_code_index = list_utils.find_index(answers[0], form_code_column_name)
    answers_start_index = list_utils.find_index(
        answers[0][form_code_index + 1:], "Q1") + form_code_index + 1
    virtual_fields: tp.List[grid_info.RealOrVirtualField] = [
        grid_info.VirtualField.SCORE, grid_info.VirtualField.POINTS
    ]
    num_questions = max([len(x) for x in keys_scores.values()])
    columns = results.field_columns + virtual_fields
    scored_results = data_exporting.OutputSheet(columns, num_questions)

    for exam in answers[1:]:  # Skip header row
        fields = {
            k: v
            for k, v in zip(results.field_columns, exam[:answers_start_index])
        }
        form_code = exam[form_code_index]
        print(form_code)
        try:
            if "*" in keys_scores:
                key, scores = zip(*keys_scores["*"])
            else:
                key, scores = zip(*keys_scores[form_code])
            if len(scores) == 0:
                scores = [1.] * len(key)
        except KeyError:
            fields[grid_info.VirtualField.
                   SCORE] = data_exporting.KEY_NOT_FOUND_MESSAGE
            fields[grid_info.VirtualField.
                   POINTS] = data_exporting.KEY_NOT_FOUND_MESSAGE
            scored_answers = []
        else:
            #print(exam[answers_start_index:], key, scores)
            scored_answers = [
                grade_answer(answer, correct, score)
                for answer, correct, score in zip(exam[answers_start_index:], key, scores)
            ]
            #TODO: implement the logic to cancel a question
            key_scores = np.array(scores)
            nan_mask = np.isnan(scored_answers)
            max_score = np.sum(key_scores[~nan_mask])
            raw_score = np.nansum(scored_answers)
            score = raw_score / max_score

            fields[grid_info.VirtualField.SCORE] = str(
                round(score * 100, 2))
            fields[grid_info.VirtualField.POINTS] = str(
                round(np.sum(key_scores) * score, 2))
        string_scored_answers = [str(s) for s in scored_answers]
        scored_results.add(fields, string_scored_answers)

    return scored_results


def verify_answer_key_sheet(file_path: pathlib.Path) -> bool:
    try:
        with open(str(file_path), newline='') as file:
            reader = csv.reader(file)
            keys_column_name = data_exporting.COLUMN_NAMES[
                grid_info.Field.TEST_FORM_CODE]
            names = next(reader)
            keys_column_name_index = list_utils.find_index(
                names, keys_column_name)
            list_utils.find_index(names[keys_column_name_index:], "Q1")
        return True
    except Exception:
        return False

def _extract_with_multiple(s:str):
    if s.startswith("[") and s.endswith("]"):
        correct_set = set(s.strip("[]").split("|"))
        return correct_set
    else:
        return s
def grade_answer(answer:str, correct:str, score:float) -> float:
    correct = _extract_with_multiple(correct)
    if correct == "*":
        return np.nan
    elif len(correct) == 1:
        return int(answer == correct) * score
    elif isinstance(correct, set):
        correct_set = correct
        answer_set = _extract_with_multiple(answer)
        if isinstance(answer_set, set):
            answer_set = {answer_set}
        return int(bool(len(correct_set.intersection(answer_set)))) * score

    elif correct.startswith("*"):
        correct = correct.replace("*", "")
        if len(correct) == 1:
            if answer == correct:
                return score
            else:
                return np.nan
        elif correct.startswith("[") and correct.endswith("]"):
            correct_set = set(correct.strip("[]"))
            if answer in correct_set:
                return score
            else:
                return np.nan
        else:
            raise NotImplementedError(f"correct *{correct} not implemented.")
    else:
        raise NotImplementedError(f"correct {correct} not implemented.")
