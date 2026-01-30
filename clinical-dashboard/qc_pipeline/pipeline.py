from pathlib import Path
import pandas as pd
import re
import os
from functools import reduce


# =================================================
# HELPERS
# =================================================

def extract_study_number(name: str):
    """Extract first integer from a string."""
    m = re.search(r"(\d+)", name)
    return int(m.group(1)) if m else None


# =================================================
# STAGE 1 — FOLDER STANDARDISATION
# =================================================

def rename_study_folders(root_dir: Path):
    DRY_RUN = False

    for folder_name in os.listdir(root_dir):
        old_path = root_dir / folder_name
        if not old_path.is_dir():
            continue

        study_number = extract_study_number(folder_name)
        if study_number is None:
            continue

        study_number = str(study_number).zfill(2)
        new_folder_name = f"Study {study_number} CPID Input Files"
        new_path = root_dir / new_folder_name

        if old_path == new_path:
            continue

        if not DRY_RUN:
            os.rename(old_path, new_path)


# =================================================
# STAGE 2 — FILE STANDARDISATION
# =================================================

def rename_files_in_study_folder(study_dir: Path):
    DRY_RUN = False

    CATEGORIES = {
        "CPID_EDC_Metrics": ["cpid"],
        "Visit Projection Tracker": ["visit projection", "missing visit"],
        "Missing Lab Name and Missing Ranges": ["missing lab", "lnr"],
        "SAE Dashboard": ["sae", "esae", "dm_safety"],
        "Inactivated Forms and Folders": ["inactivated"],
        "Global Missing Pages Report": ["missing pages"],
        "Compiled EDRR": ["edrr"],
        "GlobalCodingReport_MedDRA": ["meddra"],
        "GlobalCodingReport_WHODD": ["whodd", "whodrug"],
    }

    def detect_category(file_name: str):
        name = file_name.lower()
        for category, patterns in CATEGORIES.items():
            for pat in patterns:
                if pat in name:
                    return category
        return None

    study_num = extract_study_number(study_dir.name)
    if study_num is None:
        return

    used = set()

    for f in study_dir.iterdir():
        if not f.is_file():
            continue

        category = detect_category(f.name)
        if category is None or category in used:
            continue

        new_name = f"Study {study_num} - {category}.xlsx"
        new_path = f.with_name(new_name)

        if not new_path.exists() and not DRY_RUN:
            f.rename(new_path)

        used.add(category)


# =================================================
# STAGE 3 — ADD STUDY KEY
# =================================================

def add_study_key(root_dir: Path):
    print("Adding Study Key to all Excel files...")
    DRY_RUN = False

    for study_dir in root_dir.iterdir():
        if not study_dir.is_dir():
            continue

        study_key = extract_study_number(study_dir.name)
        if study_key is None:
            continue

        for file in study_dir.glob("*.xlsx"):
            try:
                sheets = pd.read_excel(file, sheet_name=None)
                
                for sheet, df in sheets.items():
                    df["Study Key"] = study_key
                    sheets[sheet] = df

                if not DRY_RUN:
                    with pd.ExcelWriter(file, engine="openpyxl", mode="w") as writer:
                        for sheet, df in sheets.items():
                            df.to_excel(writer, sheet_name=sheet, index=False)
            except Exception as e:
                print(f"Error processing {file}: {e}")
                continue


# =================================================
# STAGE 4 — METRIC EXTRACTION
# =================================================

def extract_cols(root_dir):
    """Extract metrics from standardized files with robust error handling"""
    
    # =================================================
    # Helpers
    # =================================================

    def standardise_subject_column(df):
        """Standardize subject column names across different file formats"""
        SUBJECT_ALIASES = [
            "subject",
            "subject name",
            "subject id",
            "patient",
            "patient id",
            "subjid",
            "participant id",
            "subjectname"
        ]

        if df is None or df.empty:
            return df

        for col in df.columns:
            if col.lower().strip() in SUBJECT_ALIASES:
                return df.rename(columns={col: "Subject"})

        # If no subject column found, try to create one from available columns
        if "Subject" not in df.columns:
            # Check if there's any column that might contain subject IDs
            for col in df.columns:
                if "id" in col.lower() or "name" in col.lower():
                    df = df.rename(columns={col: "Subject"})
                    break
        
        return df

    def group_count(file_path, col_name):
        """Group by Study Key and Subject and count occurrences"""
        try:
            df = pd.read_excel(file_path)
            df = standardise_subject_column(df)
            
            if df is None or df.empty:
                return None
                
            # Ensure required columns exist
            if "Study Key" not in df.columns:
                # Try to extract study key from file path
                study_num = extract_study_number(str(file_path))
                if study_num:
                    df["Study Key"] = study_num
                else:
                    return None
            
            if "Subject" not in df.columns:
                return None
                
            df["Study Key"] = df["Study Key"].astype(str)
            df["Subject"] = df["Subject"].astype(str)

            return (
                df.groupby(["Study Key", "Subject"])
                .size()
                .reset_index(name=col_name)
            )
        except Exception as e:
            print(f"Error in group_count for {file_path}: {e}")
            return None

    def clean_grouping_columns(df, cols):
        """Clean grouping columns to ensure consistent merging"""
        if df is None or df.empty:
            return df
            
        for col in cols:
            if col in df.columns:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.strip()
                    .replace(["", "nan", "NA", "None"], "Unknown")
                )
        return df

    def standardise_merge_keys(df):
        """Ensure merge keys are standardized"""
        if df is None or df.empty:
            return df
            
        if "Study Key" in df.columns:
            df["Study Key"] = df["Study Key"].astype(str)
        if "Subject" in df.columns:
            df["Subject"] = df["Subject"].astype(str)
        return df

    def coded_uncoded_from_file(file_path):
        """Extract coded and uncoded terms from coding reports"""
        try:
            df = pd.read_excel(file_path)
            df = standardise_subject_column(df)
            
            if df is None or df.empty:
                return None
                
            if "Coding Status" not in df.columns:
                return None
                
            df["_is_coded"] = df["Coding Status"].fillna("").eq("Coded Term")
            df["_is_uncoded"] = ~df["_is_coded"]

            return (
                df.groupby(["Study Key", "Subject"])
                .agg(
                    Coded_Terms=("_is_coded", "sum"),
                    UnCoded_Terms=("_is_uncoded", "sum")
                )
                .reset_index()
            )
        except Exception as e:
            print(f"Error in coded_uncoded_from_file for {file_path}: {e}")
            return None

    def sae_dashboard_summary_from_file(file_path):
        """Extract SAE dashboard summaries"""
        try:
            sheets = pd.read_excel(file_path, sheet_name=None)
            summaries = {}

            for sheet_name, df in sheets.items():
                df = standardise_subject_column(df)
                
                if df is None or df.empty:
                    continue
                    
                df = clean_grouping_columns(df, ["Study Key", "Subject"])

                # Check for Review Status column
                if "Review Status" not in df.columns:
                    continue
                    
                df["_is_completed"] = df["Review Status"].fillna("").eq("Review Completed")

                label = "DM" if "dm" in sheet_name.lower() else "Safety"

                summary = (
                    df.groupby(["Study Key", "Subject"])["_is_completed"]
                    .sum()
                    .reset_index(name=label)
                )

                summaries[label] = summary

            # ---- Outer merge (superset) ----
            merged = None
            for summary in summaries.values():
                if summary is not None and not summary.empty:
                    if merged is None:
                        merged = summary
                    else:
                        merged = merged.merge(
                            summary,
                            on=["Study Key", "Subject"],
                            how="outer"
                        )

            return merged
        except Exception as e:
            print(f"Error in sae_dashboard_summary_from_file for {file_path}: {e}")
            return None

    def edrr_summary_from_file(file_path):
        """Extract EDRR summaries"""
        try:
            df = pd.read_excel(file_path)
            df = standardise_subject_column(df)
            
            if df is None or df.empty:
                return None
                
            df = clean_grouping_columns(df, ["Study Key", "Subject"])

            if "Total Open issue Count per subject" not in df.columns:
                return None
                
            return df[[
                "Study Key",
                "Subject",
                "Total Open issue Count per subject"
            ]].rename(columns={
                "Total Open issue Count per subject": "EDRR"
            })
        except Exception as e:
            print(f"Error in edrr_summary_from_file for {file_path}: {e}")
            return None

    # =================================================
    # Main processing function
    # =================================================

    def process_study_folder(study_dir):
        """Process a single study folder and extract all metrics"""
        coding_summary = None
        missing_lab_summary = None
        inactivated_logs_summary = None
        sae_dashboard_summary = None
        edrr_summary = None
        missing_pages_summary = None
        missing_visits_summary = None

        # ---- Find all files ----
        meddra = list(study_dir.glob("*GlobalCodingReport_MedDRA.xlsx"))
        whodd = list(study_dir.glob("*GlobalCodingReport_WHODD.xlsx"))
        missing_lab = list(study_dir.glob("*Missing Lab Name and Missing Ranges.xlsx"))
        inactivated_logs = list(study_dir.glob("*Inactivated Forms and Folders.xlsx"))
        sae_dashboard = list(study_dir.glob("*SAE Dashboard.xlsx"))
        edrr = list(study_dir.glob("*Compiled EDRR.xlsx"))
        missing_pages = list(study_dir.glob("*Global Missing Pages Report.xlsx"))
        missing_visits = list(study_dir.glob("*Visit Projection Tracker.xlsx"))

        # ---- Coding (MedDRA + WHODD) ----
        if meddra:
            coding_summary = coded_uncoded_from_file(meddra[0])

        if whodd:
            whodd_summary = coded_uncoded_from_file(whodd[0])

            if coding_summary is None:
                coding_summary = whodd_summary
            elif whodd_summary is not None:
                coding_summary = coding_summary.merge(
                    whodd_summary,
                    on=["Study Key", "Subject"],
                    how="outer",
                    suffixes=("", "_whodd")
                )

                coding_summary["Coded_Terms"] = (
                    coding_summary["Coded_Terms"].fillna(0) +
                    coding_summary["Coded_Terms_whodd"].fillna(0)
                )

                coding_summary["UnCoded_Terms"] = (
                    coding_summary["UnCoded_Terms"].fillna(0) +
                    coding_summary["UnCoded_Terms_whodd"].fillna(0)
                )

                coding_summary = coding_summary[
                    ["Study Key", "Subject", "Coded_Terms", "UnCoded_Terms"]
                ]

        # ---- Missing Lab ----
        if missing_lab:
            missing_lab_summary = group_count(missing_lab[0], "Open Issues Count LNR")

        # ---- Inactivated Logs ----
        if inactivated_logs:
            inactivated_logs_summary = group_count(inactivated_logs[0], "Inactivated Logs")

        # ---- SAE Dashboard ----
        if sae_dashboard:
            sae_dashboard_summary = sae_dashboard_summary_from_file(sae_dashboard[0])

        # ---- EDRR ----
        if edrr:
            edrr_summary = edrr_summary_from_file(edrr[0])

        # ---- Missing Pages ----
        if missing_pages:
            missing_pages_summary = group_count(missing_pages[0], "Missing Pages")

        # ---- Missing Visits ----
        if missing_visits:
            missing_visits_summary = group_count(missing_visits[0], "Missing Visits")

        return (
            coding_summary, missing_lab_summary, edrr_summary, 
            inactivated_logs_summary, sae_dashboard_summary, 
            missing_pages_summary, missing_visits_summary
        )

    # =================================================
    # Main loop - collect all summaries
    # =================================================

    all_coding_summaries = []
    missing_lab_summaries = []
    inactivated_logs_summaries = []
    sae_dashboard_summaries = []
    edrr_summaries = []
    missing_pages_summaries = []
    missing_visits_summaries = []

    for study_dir in root_dir.iterdir():
        if not study_dir.is_dir():
            continue

        coding, missing_lab, edrr, inactivated, sae, missing_pages, missing_visits = process_study_folder(study_dir)

        if coding is not None and not coding.empty:
            all_coding_summaries.append(coding)

        if missing_lab is not None and not missing_lab.empty:
            missing_lab_summaries.append(missing_lab)

        if inactivated is not None and not inactivated.empty:
            inactivated_logs_summaries.append(inactivated)

        if sae is not None and not sae.empty:
            sae_dashboard_summaries.append(sae)

        if edrr is not None and not edrr.empty:
            edrr_summaries.append(edrr)

        if missing_pages is not None and not missing_pages.empty:
            missing_pages_summaries.append(missing_pages)

        if missing_visits is not None and not missing_visits.empty:
            missing_visits_summaries.append(missing_visits)

    # =================================================
    # Create final dataframes with error handling
    # =================================================

    def safe_concat(dataframes_list, description=""):
        """Safely concatenate a list of dataframes, handling empty lists"""
        if not dataframes_list:
            # Return an empty dataframe with expected columns
            return pd.DataFrame(columns=["Study Key", "Subject"])
        
        # Filter out None values
        valid_dfs = [df for df in dataframes_list if df is not None and not df.empty]
        
        if not valid_dfs:
            return pd.DataFrame(columns=["Study Key", "Subject"])
            
        try:
            return pd.concat(valid_dfs, ignore_index=True)
        except Exception as e:
            print(f"Error concatenating {description}: {e}")
            return pd.DataFrame(columns=["Study Key", "Subject"])

    # Create final summaries with safe concatenation
    final_coding_summary = safe_concat(all_coding_summaries, "coding summaries")
    final_missing_lab_summary = safe_concat(missing_lab_summaries, "missing lab summaries")
    final_inactivated_logs_summary = safe_concat(inactivated_logs_summaries, "inactivated logs summaries")
    final_sae_dashboard_summary = safe_concat(sae_dashboard_summaries, "SAE dashboard summaries")
    final_edrr_summary = safe_concat(edrr_summaries, "EDRR summaries")
    final_missing_pages_summary = safe_concat(missing_pages_summaries, "missing pages summaries")
    final_missing_visits_summary = safe_concat(missing_visits_summaries, "missing visits summaries")

    # =================================================
    # Prepare dataframes for merging
    # =================================================

    # Rename columns for consistency
    coding_df = final_coding_summary.rename(columns={
        "Coded_Terms": "Coded",
        "UnCoded_Terms": "UnCoded"
    }) if not final_coding_summary.empty else pd.DataFrame(columns=["Study Key", "Subject", "Coded", "UnCoded"])

    lnr_df = final_missing_lab_summary.rename(columns={
        "Open Issues Count LNR": "LnR"
    }) if not final_missing_lab_summary.empty else pd.DataFrame(columns=["Study Key", "Subject", "LnR"])

    inactivated_df = final_inactivated_logs_summary.rename(columns={
        "Inactivated Logs": "Inactivated"
    }) if not final_inactivated_logs_summary.empty else pd.DataFrame(columns=["Study Key", "Subject", "Inactivated"])

    edrr_df = final_edrr_summary if not final_edrr_summary.empty else pd.DataFrame(columns=["Study Key", "Subject", "EDRR"])
    
    sae_df = final_sae_dashboard_summary if not final_sae_dashboard_summary.empty else pd.DataFrame(columns=["Study Key", "Subject", "DM", "Safety"])
    
    missing_pages_df = final_missing_pages_summary if not final_missing_pages_summary.empty else pd.DataFrame(columns=["Study Key", "Subject", "Missing Pages"])
    
    missing_visits_df = final_missing_visits_summary if not final_missing_visits_summary.empty else pd.DataFrame(columns=["Study Key", "Subject", "Missing Visits"])

    # =================================================
    # Standardize merge keys
    # =================================================

    tables = []
    
    for df, name in [
        (coding_df, "Coding"),
        (lnr_df, "LNR"),
        (edrr_df, "EDRR"),
        (inactivated_df, "Inactivated"),
        (sae_df, "SAE"),
        (missing_pages_df, "Missing Pages"),
        (missing_visits_df, "Missing Visits")
    ]:
        if not df.empty:
            df = standardise_merge_keys(df)
            tables.append(df)
            print(f"Added {name} table with {len(df)} rows")
        else:
            print(f"Skipping empty {name} table")

    # =================================================
    # Merge all tables
    # =================================================

    if not tables:
        print("No data found in any tables")
        return pd.DataFrame(columns=["Study Key", "Subject"])

    # Start with first table
    final_master_qc = tables[0]
    
    # Merge remaining tables
    for i, df in enumerate(tables[1:], 1):
        try:
            final_master_qc = pd.merge(
                final_master_qc,
                df,
                on=["Study Key", "Subject"],
                how="outer"
            )
        except Exception as e:
            print(f"Error merging table {i}: {e}")
            continue

    # =================================================
    # Final processing
    # =================================================

    # Define all possible metric columns
    all_metric_cols = [
        "Coded", "UnCoded", "LnR", "EDRR", "Inactivated", 
        "DM", "Safety", "Missing Pages", "Missing Visits"
    ]

    # Add missing columns with 0 values
    for col in all_metric_cols:
        if col not in final_master_qc.columns:
            final_master_qc[col] = 0

    # Fill NaN values with 0
    final_master_qc = final_master_qc.fillna(0)

    # Convert metric columns to integers
    for col in all_metric_cols:
        if col in final_master_qc.columns:
            final_master_qc[col] = final_master_qc[col].astype(int)

    # Sort and order columns
    final_master_qc = final_master_qc[
        ["Study Key", "Subject"] + all_metric_cols
    ].sort_values(["Study Key", "Subject"])

    print(f"Final QC DataFrame shape: {final_master_qc.shape}")
    print(f"Final QC DataFrame columns: {final_master_qc.columns.tolist()}")
    
    return final_master_qc


# =================================================
# MAIN PIPELINE ENTRY
# =================================================

def run_qc_pipeline(root_dir):
    """
    Entry point used by Streamlit.
    root_dir: Path or str
    """
    root_dir = Path(root_dir)
    
    if not root_dir.exists():
        raise ValueError(f"Directory does not exist: {root_dir}")
    
    print(f"Running QC pipeline on: {root_dir}")
    
    try:
        # Stage 1: Rename folders
        print("Stage 1: Renaming study folders...")
        rename_study_folders(root_dir)
        
        # Stage 2: Rename files
        print("Stage 2: Renaming files in study folders...")
        for study_dir in root_dir.iterdir():
            if study_dir.is_dir():
                rename_files_in_study_folder(study_dir)
        
        # Stage 3: Add study key
        print("Stage 3: Adding study keys...")
        add_study_key(root_dir)
        
        # Stage 4: Extract metrics
        print("Stage 4: Extracting metrics...")
        final_qc_df = extract_cols(root_dir)
        
        if final_qc_df.empty:
            print("Warning: No data extracted. Check input files.")
        else:
            print(f"Extracted {len(final_qc_df)} rows")
            print(final_qc_df.head())
        
        return final_qc_df
        
    except Exception as e:
        print(f"Error in QC pipeline: {e}")
        raise