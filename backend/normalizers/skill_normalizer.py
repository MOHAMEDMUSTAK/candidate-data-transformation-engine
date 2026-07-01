from __future__ import annotations

"""
Eightfold AI - Skill Normalizer

Canonicalizes skill names using a dictionary of known aliases.
Handles common variations: JS→JavaScript→React, ML→Machine Learning, etc.
"""

import logging
from typing import Any

from backend.models.provenance import RuleApplication

logger = logging.getLogger(__name__)

# Canonical skill dictionary — maps aliases to canonical names
# Every alias maps to exactly one canonical form for determinism
SKILL_CANONICAL_MAP: dict[str, str] = {
    # JavaScript ecosystem
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ecmascript": "JavaScript",
    "es6": "JavaScript",
    "es2015": "JavaScript",
    "reactjs": "React",
    "react.js": "React",
    "react js": "React",
    "react": "React",
    "reactnative": "React Native",
    "react native": "React Native",
    "react-native": "React Native",
    "vuejs": "Vue.js",
    "vue.js": "Vue.js",
    "vue": "Vue.js",
    "angularjs": "Angular",
    "angular.js": "Angular",
    "angular": "Angular",
    "angular2": "Angular",
    "nextjs": "Next.js",
    "next.js": "Next.js",
    "next": "Next.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "node": "Node.js",
    "expressjs": "Express.js",
    "express.js": "Express.js",
    "express": "Express.js",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "jquery": "jQuery",

    # Python ecosystem
    "python": "Python",
    "python3": "Python",
    "python2": "Python",
    "py": "Python",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "fast api": "FastAPI",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "scipy": "SciPy",
    "scikit-learn": "Scikit-learn",
    "sklearn": "Scikit-learn",
    "scikit learn": "Scikit-learn",

    # AI/ML
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "machinelearning": "Machine Learning",
    "dl": "Deep Learning",
    "deep learning": "Deep Learning",
    "deeplearning": "Deep Learning",
    "ai": "Artificial Intelligence",
    "artificial intelligence": "Artificial Intelligence",
    "nlp": "Natural Language Processing",
    "natural language processing": "Natural Language Processing",
    "cv": "Computer Vision",
    "computer vision": "Computer Vision",
    "tensorflow": "TensorFlow",
    "tf": "TensorFlow",
    "pytorch": "PyTorch",
    "torch": "PyTorch",
    "keras": "Keras",
    "llm": "Large Language Models",
    "large language models": "Large Language Models",
    "generative ai": "Generative AI",
    "genai": "Generative AI",

    # Java ecosystem
    "java": "Java",
    "spring": "Spring",
    "spring boot": "Spring Boot",
    "springboot": "Spring Boot",
    "hibernate": "Hibernate",

    # Databases
    "sql": "SQL",
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch",
    "elastic search": "Elasticsearch",
    "dynamodb": "DynamoDB",
    "dynamo db": "DynamoDB",
    "cassandra": "Cassandra",
    "sqlite": "SQLite",
    "nosql": "NoSQL",

    # Cloud & DevOps
    "aws": "AWS",
    "amazon web services": "AWS",
    "azure": "Azure",
    "microsoft azure": "Azure",
    "gcp": "GCP",
    "google cloud": "GCP",
    "google cloud platform": "GCP",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "terraform": "Terraform",
    "ansible": "Ansible",
    "jenkins": "Jenkins",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "ci cd": "CI/CD",
    "devops": "DevOps",
    "dev ops": "DevOps",

    # Other languages
    "c++": "C++",
    "cpp": "C++",
    "c#": "C#",
    "csharp": "C#",
    "c sharp": "C#",
    "golang": "Go",
    "go": "Go",
    "rust": "Rust",
    "kotlin": "Kotlin",
    "swift": "Swift",
    "ruby": "Ruby",
    "php": "PHP",
    "scala": "Scala",
    "r": "R",
    "matlab": "MATLAB",
    "bash": "Bash",
    "shell": "Shell Scripting",
    "shell scripting": "Shell Scripting",
    "powershell": "PowerShell",

    # Web technologies
    "html": "HTML",
    "html5": "HTML",
    "css": "CSS",
    "css3": "CSS",
    "sass": "Sass",
    "scss": "Sass",
    "less": "Less",
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
    "tailwind css": "Tailwind CSS",
    "bootstrap": "Bootstrap",
    "webpack": "Webpack",
    "vite": "Vite",

    # Methodologies
    "agile": "Agile",
    "scrum": "Scrum",
    "kanban": "Kanban",
    "tdd": "TDD",
    "test driven development": "TDD",
    "bdd": "BDD",

    # Other tools/concepts
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "bitbucket": "Bitbucket",
    "jira": "Jira",
    "confluence": "Confluence",
    "rest": "REST",
    "restful": "REST",
    "rest api": "REST",
    "graphql": "GraphQL",
    "grpc": "gRPC",
    "microservices": "Microservices",
    "micro services": "Microservices",
    "api": "API Design",
    "linux": "Linux",
    "unix": "Unix",
    "data structures": "Data Structures",
    "algorithms": "Algorithms",
    "dsa": "Data Structures & Algorithms",
    "system design": "System Design",
    "figma": "Figma",
    "spark": "Apache Spark",
    "apache spark": "Apache Spark",
    "kafka": "Apache Kafka",
    "apache kafka": "Apache Kafka",
    "hadoop": "Hadoop",
    "airflow": "Apache Airflow",
    "apache airflow": "Apache Airflow",
}


def normalize_skill(
    skill: str,
    rules_log: list[RuleApplication] | None = None,
) -> str:
    """
    Normalize a single skill name to its canonical form.

    Args:
        skill: Raw skill name
        rules_log: Optional list to record applied rules

    Returns:
        Canonical skill name (original if no mapping exists)
    """
    original = skill
    skill = skill.strip()
    if not skill:
        return original

    lookup = skill.lower().strip()

    if lookup in SKILL_CANONICAL_MAP:
        canonical = SKILL_CANONICAL_MAP[lookup]
        if canonical != original:
            if rules_log is not None:
                rules_log.append(RuleApplication(
                    rule_name="skill_canonicalize",
                    rule_category="skill",
                    description=f"Skill '{original}' canonicalized to '{canonical}'",
                    field="skills",
                    original_value=original,
                    transformed_value=canonical,
                    stage="canonicalization",
                ))
        return canonical

    # Title-case the skill if not found in dictionary
    title_cased = skill.title()
    if title_cased != original:
        if rules_log is not None:
            rules_log.append(RuleApplication(
                rule_name="skill_title_case",
                rule_category="skill",
                description=f"Skill '{original}' title-cased to '{title_cased}'",
                field="skills",
                original_value=original,
                transformed_value=title_cased,
                stage="canonicalization",
            ))
    return title_cased


def normalize_skills(
    skills: list[str],
    rules_log: list[RuleApplication] | None = None,
) -> tuple[list[str], int]:
    """
    Normalize and deduplicate a list of skill names.

    Returns:
        Tuple of (canonical_skills, duplicates_removed_count)
    """
    normalized: list[str] = []
    seen: set[str] = set()
    duplicates = 0

    for skill in skills:
        canonical = normalize_skill(skill, rules_log)
        if not canonical:
            continue
        lower_canonical = canonical.lower()
        if lower_canonical in seen:
            duplicates += 1
            if rules_log is not None:
                rules_log.append(RuleApplication(
                    rule_name="remove_duplicate_skill",
                    rule_category="skill",
                    description=f"Duplicate skill '{canonical}' removed",
                    field="skills",
                    original_value=skill,
                    transformed_value=None,
                    stage="canonicalization",
                ))
            continue
        seen.add(lower_canonical)
        normalized.append(canonical)

    return sorted(normalized), duplicates
