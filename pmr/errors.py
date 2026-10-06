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
    elif reason.startswith(
        ("Expected number at ", "Expected a finite number", "Currency must ", "Invalid currency", "Invalid numerical data at ", "Required allocation ratios")
    ):
        title = "Invalid numerical data"
        message = "A required financial value is missing or invalid. The app will not guess a value or silently round it."
        action = "Check the original spreadsheet using Technical Details below. Correct the source value and generate a new draft."
    elif reason.startswith(("Required sheets missing", "Required label", "Required performance summary", "Column ",
                            "Header ", "Ambiguous column", "Performance summary portfolio", "Benchmark row",
                            "No funded holdings", "Required Strategic", "Diversification category", "Required annualized")):
        title = "Required table structure is missing or ambiguous"
        message = "The source package does not contain an unambiguous table or label needed for this report."
        action = "Check the file, sheet, and label in Technical Details. Restore the required structure and generate again; do not guess a matching column or row."
    elif reason.startswith("Unexpected generation failure"):
        title = "Unexpected application error"
        message = "The application stopped unexpectedly. No completed report was released for this run."
        action = "Keep the input package unchanged and inspect the stage diagnostics or contact the developer. This is not necessarily a problem with your data."
    elif reason.startswith("Local file operation failed"):
        title = "File access failed"
        message = "A source or output file could not be opened or written."
        action = "Check folder permissions, available disk space, and whether the file is locked by another program, then run again."
    elif reason.startswith("Unreadable source workbooks") or reason in {"File is not a zip file", "File is not a ZIP file"}:
        title = "Source document is damaged or unreadable"
        message = "A required workbook or presentation could not be read."
        action = "Extract a fresh copy of the input package and verify the indicated files open normally before generating again."
    elif reason.startswith("Output folder must be separate"):
        title = "Choose a separate output folder"
        message = "Reports cannot be written inside the source-document folder."
        action = "Choose an output folder outside the inputs folder and run again."
    elif reason.startswith("Source folder does not exist"):
        title = "Source folder is unavailable"
        message = "The selected source folder cannot be found or is not a folder."
        action = "Select the extracted document package folder and generate again."
    elif reason.startswith("Source files changed during generation"):
        title = "Source documents changed during the run"
        message = "The input package changed while the report was being generated. Its evidence can no longer be verified consistently."
        action = (
            "Finish editing the source documents, then generate again without changing them during the run."
        )
    elif reason.startswith("Implementation changed during generation"):
        title = "Application updated during the run"
        message = "The reporting code changed during generation, so this run was stopped to protect reproducibility."
        action = "Wait until the code changes are complete, then generate a new report."
    return dict(error_title=title, error=message, error_action=action, error_details=reason)
