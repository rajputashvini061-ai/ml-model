"""Utility script to synchronize course metadata and eligibility columns in courses.csv."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DATASET_PATH = Path(__file__).resolve().parent / "courses.csv"

# Course-wise mapping
course_data = {
    "Civil Engineering": {
        "interests": "Construction;Infrastructure;Buildings;Bridges;Structural Design",
        "skills": "Problem Solving;Planning;Design;Spatial Thinking",
        "subjects": "Engineering Mechanics;Surveying;Structural Engineering;Building Materials",
        "career_paths": "Civil Engineer;Structural Engineer;Site Engineer;Construction Manager",
    },
    "Computer Science and Engineering": {
        "interests": "Software Development;Programming;Technology;Applications",
        "skills": "C Programming;Python;Logical Thinking;Problem Solving",
        "subjects": "Programming;Data Structures;DBMS;Operating Systems",
        "career_paths": "Software Developer;Web Developer;System Engineer",
    },
    "Computer Science and Information Technology": {
        "interests": "Information Technology;Networking;Software;Database Systems",
        "skills": "Programming;Networking;Database Management;Troubleshooting",
        "subjects": "Programming;Computer Networks;DBMS;Operating Systems",
        "career_paths": "IT Engineer;Network Administrator;Database Developer",
    },
    "CSE with Artificial Intelligence and Data Science": {
        "interests": "Artificial Intelligence;Data Science;Data Analytics;Statistics;Machine Learning",
        "skills": "Python;Statistics;Data Analysis;Logical Thinking",
        "subjects": "Mathematics;Statistics;Python;Machine Learning",
        "career_paths": "Data Analyst;Data Scientist;AI Engineer;ML Engineer",
    },
    "CSE with Artificial Intelligence and Machine Learning": {
        "interests": "Artificial Intelligence;Machine Learning;Deep Learning;Robotics;Automation",
        "skills": "Python;Programming;Mathematics;Algorithmic Thinking",
        "subjects": "Mathematics;Machine Learning;Deep Learning;Algorithms",
        "career_paths": "Machine Learning Engineer;AI Engineer;AI Research Assistant",
    },
    "CSE with Artificial Intelligence and Internet of Things": {
        "interests": "IoT;Smart Devices;Robotics;Automation;Embedded Systems",
        "skills": "Python;Programming;Electronics;Problem Solving",
        "subjects": "Computer Networks;Sensors;Embedded Systems;Programming",
        "career_paths": "IoT Developer;Embedded Systems Engineer;Automation Engineer",
    },
    "CSE with Cyber Security": {
        "interests": "Cyber Security;Information Security;Network Security;Digital Safety",
        "skills": "Programming;Networking;Logical Thinking;Problem Solving",
        "subjects": "Computer Networks;Operating Systems;Cryptography",
        "career_paths": "Cyber Security Analyst;Security Engineer;Network Security Analyst",
    },
    "Electrical and Electronics Engineering": {
        "interests": "Electrical Systems;Electronics;Automation;Power Technology",
        "skills": "Circuit Analysis;Problem Solving;Technical Skills",
        "subjects": "Electrical Circuits;Power Systems;Electronics",
        "career_paths": "Electrical Engineer;Electronics Engineer;Automation Engineer",
    },
    "Electrical Engineering": {
        "interests": "Power Systems;Electrical Machines;Energy;Power Generation",
        "skills": "Electrical Design;Circuit Analysis;Problem Solving",
        "subjects": "Electrical Machines;Power Systems;Control Systems",
        "career_paths": "Electrical Engineer;Power Systems Engineer;Maintenance Engineer",
    },
    "Electronics and Communication Engineering": {
        "interests": "Electronics;Communication;Embedded Systems;Signal Processing",
        "skills": "Electronics;Circuit Design;Programming;Problem Solving",
        "subjects": "Digital Electronics;Electronic Devices;Communication Systems",
        "career_paths": "Electronics Engineer;Communication Engineer;Embedded Engineer",
    },
    "Mechanical Engineering": {
        "interests": "Automobiles;Machines;Manufacturing;Product Design;Robotics",
        "skills": "CAD;Technical Design;Problem Solving;Mechanical Analysis",
        "subjects": "Thermodynamics;Engineering Mechanics;Manufacturing",
        "career_paths": "Mechanical Engineer;Design Engineer;Production Engineer",
    },
    "Bachelor of Pharmacy": {
        "interests": "Healthcare;Medicines;Pharmaceutical Science;Chemistry",
        "skills": "Scientific Analysis;Laboratory Skills;Research;Attention to Detail",
        "subjects": "Pharmaceutics;Pharmaceutical Chemistry;Pharmacology",
        "career_paths": "Pharmacist;Pharmaceutical Researcher;Quality Control Analyst",
    },
    "Bachelor of Business Administration": {
        "interests": "Business;Entrepreneurship;Marketing;Management;Finance",
        "skills": "Communication;Leadership;Business Analysis;Decision Making",
        "subjects": "Accounting;Marketing;Business Management;Economics",
        "career_paths": "Business Executive;Marketing Executive;Business Analyst;Entrepreneur",
    },
}

# Stream-wise eligibility mapping
btech_courses = [
    "Civil Engineering",
    "Computer Science and Engineering",
    "Computer Science and Information Technology",
    "CSE with Artificial Intelligence and Data Science",
    "CSE with Artificial Intelligence and Machine Learning",
    "CSE with Artificial Intelligence and Internet of Things",
    "CSE with Cyber Security",
    "Electrical and Electronics Engineering",
    "Electrical Engineering",
    "Electronics and Communication Engineering",
    "Mechanical Engineering",
]

eligibility_data = {
    course: {
        "eligible_streams": "PCM;PCMB",
        "required_subjects": "Physics;Chemistry;Mathematics",
        "eligibility_criteria": (
            "10+2 from recognized board with Physics and Chemistry "
            "and Mathematics/Biology/Biotechnology; "
            "branch-specific admission rules must be verified "
            "through current DTE/RGPV guidelines."
        ),
    }
    for course in btech_courses
}

eligibility_data["Bachelor of Pharmacy"] = {
    "eligible_streams": "PCB;PCMB",
    "required_subjects": "Physics;Chemistry;Biology",
    "eligibility_criteria": (
        "10+2 with Physics and Chemistry along with Mathematics "
        "or Biology; final eligibility as per current DTE and PCI norms."
    ),
}

eligibility_data["Bachelor of Business Administration"] = {
    "eligible_streams": "PCM;PCB;PCMB;Commerce;Arts",
    "required_subjects": "10+2 pass",
    "eligibility_criteria": "Passed Class 12 from any stream and recognized board.",
}


def update_courses_csv(csv_path: Path = DATASET_PATH) -> pd.DataFrame:
    """Update courses.csv safely while preserving existing columns and values."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found at: {csv_path}")

    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)

    required_columns = [
        "interests",
        "skills",
        "subjects",
        "career_paths",
        "eligible_streams",
        "required_subjects",
        "eligibility_criteria",
        "eligibility_source",
    ]
    for column in required_columns:
        if column not in df.columns:
            df[column] = ""
        df[column] = df[column].fillna("").astype(str)

    for index, row in df.iterrows():
        programme = row["programme"]
        if programme in course_data:
            for column, value in course_data[programme].items():
                df.at[index, column] = value
        if programme in eligibility_data:
            for column, value in eligibility_data[programme].items():
                df.at[index, column] = value

    df.to_csv(csv_path, index=False)
    return df


if __name__ == "__main__":
    updated_df = update_courses_csv()
    print("Course mapping updated successfully!")
    print("Total courses:", len(updated_df))
    print("\nUpdated course data:")
    print(updated_df[["programme", "interests", "skills"]].to_string(index=False))
