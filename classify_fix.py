#!/usr/bin/env python3
"""Correct subject classification shared by scrape.py and the data repair.

Newer CRDP PDFs have a filename like SV_Bio_2021_1_En.pdf, where the second
token is the authoritative subject. Older PDFs have numeric names, so the
title is parsed instead. Titles of newer papers begin with the *branch* name
(e.g. "علوم الحياة - اللغة الفرنسية - 2021"), which must be ignored or every
SV paper is wrongly filed as Biology.
"""
import re

# PDF filename token -> subject key.
FILENAME_SUBJECTS = {
    "phys": "physics", "chim": "chemistry", "math": "math", "bio": "biology",
    "philo": "philosophy", "philogen": "philosophy", "philoarabe": "arabic_philosophy",
    "fran": "french", "tarikh": "history", "geo": "geography",
    "arabe": "arabic", "tarbia": "civics", "eng": "english",
    "socio": "sociology", "eco": "economics",
}

NEWER_PREFIXES = {"BR", "SE", "SG", "SV", "LH", "SELH", "SVSG"}

SUBJECT_PATTERNS = [
    ("arabic_philosophy", ["فلسفة عربية", "فلسفة عربية (فلسفة عامة)"]),
    ("philosophy", ["فلسفة", "philosophy", "philo"]),
    ("math", ["رياضيات", "math"]),
    ("physics", ["فيزياء", "physics", "physique"]),
    ("chemistry", ["كيمياء", "كيميا", "chemistry", "chimie"]),
    ("biology", ["علوم الحياة والأرض", "علوم الحياة", "علوم طبيعية", "أحياء", "biology"]),
    ("history", ["تاريخ", "history", "histoire"]),
    ("geography", ["جغرافيا", "geography", "géographie"]),
    ("civics", ["تربية وطنية", "تربية مدنية", "نربية وطنية", "التنشئة المدنية",
                "تنشئة مدنية", "civic"]),
    ("economics", ["اقتصاد", "إقتصاد", "economics", "économie"]),
    ("sociology", ["اجتماع", "إجتماع", "sociologie", "sociology"]),
    ("french", ["اللغة الفرنسية", "اللغة الفرنسية", "فرنسية", "فرنسي",
                "français", "francais", "french"]),
    ("english", ["اللغة الانكليزية", "اللغة الإنكليزية", "اللغة الإنكليرية",
                 "إنكليزية", "انكليزية", "إنكليزي", "انكليزي", "إنكليرية",
                 "english", "anglais"]),
    ("arabic", ["اللغة العربية", "العربية وآدابها", "عربية", "عربي", "arabic"]),
]

# Leading labels in CRDP titles that identify the branch, not the subject.
BRANCH_LABELS = {
    "الشهادة المتوسطة", "شهادة متوسطة", "اجتماع واقتصاد", "اجتماع وإقتصاد",
    "علوم عامة", "علوم الحياة", "آداب وانسانيات", "آداب وإنسانيات",
    "اداب و انسانيات", "اداب وانسانيات",
    "se", "sg", "sv", "sh", "lh", "selh", "svsg", "br",
}
SESSION_LABELS = re.compile(
    r"^(?:دورة|العادية|الاستثنائية|الخاصة|الكل|any|-|\d+|20\d\d|19\d\d)", re.I)
SPECIAL_LABELS = re.compile(r"احتياجات خاصة|مكفوفين|special|blind", re.I)

SEPARATOR = re.compile(r"\s*[-–—]\s*")


def filename_token(url):
    name = url.rsplit("/", 1)[-1]
    parts = name.split("_")
    if len(parts) > 1 and parts[0].upper() in NEWER_PREFIXES:
        return parts[1].lower()
    return None


BRANCH_AT_START = re.compile(
    r"^\s*(?:" + "|".join(re.escape(x) for x in sorted(
        BRANCH_LABELS, key=len, reverse=True)) + r")\s*[-–—]\s*", re.I)


def subject_from_title(title):
    # Drop the leading branch label once; it can otherwise look like a
    # subject ("علوم الحياة - اللغة الفرنسية" is French, not Biology).
    cleaned = BRANCH_AT_START.sub("", title)
    segments = []
    for segment in SEPARATOR.split(cleaned):
        seg = SPECIAL_LABELS.sub("", " ".join(segment.split())).strip().lower()
        if seg and not SESSION_LABELS.match(seg):
            segments.append(seg)

    # First pass ignores any remaining branch labels; the second pass allows
    # them, for titles where the branch word is also the subject.
    for ignore_branch in (True, False):
        for seg in segments:
            if ignore_branch and seg in BRANCH_LABELS:
                continue
            for key, needles in SUBJECT_PATTERNS:
                if any(n.lower() in seg for n in needles):
                    return key
    return None


def detect_subject(title, url=""):
    token = filename_token(url)
    if token in FILENAME_SUBJECTS:
        return FILENAME_SUBJECTS[token]
    return subject_from_title(title)
