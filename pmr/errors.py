"""Explain known validation failures without hiding their original diagnostics."""
import re


def explain_failure(reason, client, period):
    reason = str(reason)
    title = "Report generation stopped"
    message = "A required input could not be validated. No completed report was released for this run."
    action = "Open Technical Details below, check the indicated source data, then start a new report."
    match = re.fullmatch(r"Expected one populated flash for .+, found (\d+)", reason)
    if match:
        count = int(match.group(1))
        if count == 0:
            title = "Quarterly spreadsheet not found"
            message = f"No quarterly spreadsheet found for {client}, {period}, in the selected source folder."
            action = "Check the client code and quarter in New Report. Under Source Documents, select the package containing that client's quarterly flash spreadsheet. Files are matched by their contents, not just their names."
        else:
            title = "More than one matching spreadsheet"
            message = f"Found {count} quarterly spreadsheets for {client}, {period}. The app cannot safely choose one."
            action = "Create a source folder containing only the intended document package, then generate again. Renaming duplicate files will not resolve this."
    elif reason == "No prior client PMR found; policy and format cannot be established":
        title = "Previous report is missing"
        message = f"No usable previous-quarter report was found for {client}. Its policies and report format are required."
        action = "Add this client's prior PMR PDF to the selected source package, then generate again. An archived placeholder is not a usable report."
    elif reason == "Ambiguous most recent prior client PMR":
        title = "Previous report is ambiguous"
        message = f"More than one report could be the most recent prior PMR for {client}."
        action = "Keep the intended prior-quarter report in the source package and move conflicting copies to another folder, then generate again."
    elif reason.startswith(("Expected number at ", "Expected a finite number", "Currency must ", "Invalid currency")):
        title = "Invalid numerical data"
        message = "A required financial value is missing or invalid. The app will not guess a value or silently round it."
        action = "Check the original spreadsheet using Technical Details below. Correct the source value and generate a new draft."
    elif reason.startswith("Source files changed during generation"):
        title = "Source documents changed during the run"
        message = "The input package changed while the report was being generated. Its evidence can no longer be verified consistently."
        action = "Finish editing the source documents, then generate again without changing them during the run."
    elif reason.startswith("Implementation changed during generation"):
        title = "Application updated during the run"
        message = "The reporting code changed during generation, so this run was stopped to protect reproducibility."
        action = "Wait until the code changes are complete, then generate a new report."
    return dict(error_title=title, error=message, error_action=action, error_details=reason)
