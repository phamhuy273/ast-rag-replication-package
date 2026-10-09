import json
import os
import hashlib
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    extracted_path = root / "dataset" / "extracted_jd_skills.json"
    jd_raw_dir = root / "dataset" / "jd_raw"
    out_path = root / "dataset" / "queries_frozen.json"

    with open(extracted_path, "r", encoding="utf-8") as f:
        extracted = json.load(f)

    metadata = {
        "version": "1.0",
        "status": "FROZEN_PRE_REGISTRATION",
        "date": "2026-10-09",
        "governing_rules": ["R13", "R16", "R22", "R27"],
        "provenance": {
            "source_platforms": "Real-world tech recruitment platforms in Vietnam (TopCV, ITviec, VietnamWorks)",
            "collection_date": "September 2026",
            "extractor_model": "gemini-1.5-flash",
            "extraction_prompt": "Analyze the following Job Description (JD) text and extract structured technical competencies conforming to the schema: title (string), level (string), domain (string), summary (string), mandatory_skills (list of objects with skill_name, category, importance, weight), preferred_skills (list of objects with skill_name, category, importance, weight).",
            "primary_query_format": "Job Title: {title}. Domain: {domain}. Mandatory Technical Skills: {mandatory_skills}.",
            "sensitivity_query_format": "Raw full text of Job Description file"
        },
        "queries": {}
    }

    for jd_id, data in sorted(extracted.items()):
        fname = data.get("filename")
        raw_file_path = jd_raw_dir / fname
        assert raw_file_path.exists(), f"Raw file not found: {raw_file_path}"

        with open(raw_file_path, "r", encoding="utf-8") as rf:
            raw_text = rf.read()
        raw_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

        raw_mand = data.get("mandatory_skills", [])
        mand_skills = [s["skill_name"] if isinstance(s, dict) else str(s) for s in raw_mand]
        skills_str = ", ".join(mand_skills)

        title = data.get("title", "")
        domain = data.get("domain", "")
        primary_query = f"Job Title: {title}. Domain: {domain}. Mandatory Technical Skills: {skills_str}."

        raw_pref = data.get("preferred_skills", [])
        pref_skills = [s["skill_name"] if isinstance(s, dict) else str(s) for s in raw_pref]

        metadata["queries"][jd_id] = {
            "jd_id": jd_id,
            "category": data.get("category", "JAVA" if "JAVA" in jd_id else "REACT"),
            "title": title,
            "domain": domain,
            "level": data.get("level", ""),
            "mandatory_skills": mand_skills,
            "preferred_skills": pref_skills,
            "primary_query": primary_query,
            "sensitivity_raw_file": f"dataset/jd_raw/{fname}",
            "sensitivity_raw_sha256": raw_hash,
            "sensitivity_raw_text": raw_text
        }

    with open(out_path, "w", encoding="utf-8") as out_f:
        json.dump(metadata, out_f, indent=2, ensure_ascii=False)

    with open(out_path, "rb") as f:
        frozen_hash = hashlib.sha256(f.read()).hexdigest()

    print(f"Generated {out_path} with {len(metadata['queries'])} JDs.")
    print(f"queries_frozen.json SHA-256: {frozen_hash}")

if __name__ == "__main__":
    main()
