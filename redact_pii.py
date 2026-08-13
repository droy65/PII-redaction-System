#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from docx import Document
from faker import Faker

PERSON_NAMES = ['Sarthak Malvadkar', 'Kushal Subbayya Hegde', 'Pushpa Kushal Hegde', 'Rajesh Kushal Hegde', 'Rohit Kushal Hegde', 'Rakhi Girija Shetty', 'Maithili Rajesh Hegde', 'Katyayani Balasubramanian', 'Rupal K. Sancheti', 'Salil Ajay Bhargava', 'Jabeen Ajay Menon', 'Ajay Menon', 'Sunil Nagayya Shetty', 'Dinesh Hirachand Munot', 'Ajay Shriram Patil', 'Ram Kumar Tiwari', 'Indu Jacob', 'Lokesh Shah', 'Soumavo Sarkar', 'Kishan Rastogi', 'Abhijit Diwan', 'Prakash Boricha', 'Shanti Gopalkrishnan', 'Eric Bacha', 'Sachin Gawade', 'Pravin Teli', 'Siddharth Jadhav', 'Tushar Gavankar', 'Varun Badai', 'Hitesh Ramani', 'Chitra Raste', 'Sharmila Joshi', 'Cherag Gyara', 'Manisha Shukla', 'Tushar Wakhele', 'Ashish Mathew Pulloor', 'Anand Soni', 'Parag Pansare', 'Sangeeta Ramprasad Rai', 'Jayaram Shetty', 'Karunakar Bhandary', 'Karunakar Hegde', 'Narayana B. Shetty', 'Vijay Hegde', 'DM Shetty', 'Gopal BO', 'SA Shetty']

COMPANY_NAMES = ['KSH International Limited', 'KSH International Private Limited', 'Bhandary Metal Extrusion Private Limited', 'Nuvama Wealth Management Limited', 'ICICI Securities Limited', 'MUFG Intime India Private Limited', 'Link Intime India Private Limited', 'Trilegal', 'HDFC Bank Limited', 'ICICI Bank Limited', 'ICICI Bank', 'Kirtane & Pandit LLP', 'Export-Import Bank of India', 'IndusInd Bank Limited', 'State Bank of India', 'The Federal Bank Limited', 'Bajaj Finance Limited', 'Bajaj Finserv', 'CARE Analytics and Advisory Private Limited', 'CARE Ratings Limited', 'National Securities Depository Limited', 'National Payments Corporation of India', 'Reserve Bank of India', 'BSE Limited', 'National Stock Exchange of India Limited', 'Nuvama', 'ICICI Securities', 'Waterloo Industrial Park VI Private Limited', 'Waterloo Motors Private Limited', 'KSH Project Management Services Private Limited', 'KSH Infra Park 5 Private Limited', 'KSH Infra Park VI Private Limited', 'KSH Distriparks Private Limited', 'KSH Integrated Logistics Private Limited', 'Kushal Motors and Electricals Private Limited', 'Waterloo Industrial Park I Private Limited', 'Waterloo Industrial Park II Private Limited', 'Waterloo Industrial Park III Private Limited', 'Waterloo Industrial Park IV Private Limited', 'Waterloo Industrial Park V Private Limited', 'Waterloo Industrial Park VIII Private Limited', 'Waterloo Industrial Park IX Private Limited', 'Waterloo Industrial Park IX B Private Limited', 'Waterloo Industrial Park IX A Private Limited', 'KSH Infra Park IV Private Limited', 'Nidec Industrial Automation India Private Limited', 'Precision Wires India Limited', 'Bharat Bijlee Limited', 'Elantas Beck India Limited', 'Hindalco Industries Limited', 'Vedanta Limited', 'Malabar India Fund Limited', 'Georgia Transformer Corporation', 'Virginia Transformer Corporation', 'Savli Copper Products Private Limited', 'Solar Energy Corporation of India', 'Cindus Corporation', 'Dhaulagiri Family Trust', 'Everest Family Trust', 'Makalu Family Trust', 'Broad Family Trust', 'Annapurna Family Trust', 'Kanchenjunga Family Trust', 'Shubhkamal Leasing and Investment Private Limited', 'Parijat Foundation', 'Kushal Electricals', 'Waterloo Motors']

EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
SSN_RE = re.compile(r"\b\d{3}[- ]\d{2}[- ]\d{4}\b")
DOB_RE = re.compile(
    r"(?i)\b(?:date\s+of\s+birth|dob)\s*[:\-]?"
    r"(?:\s*)(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4})"
)
PHONE_RE = re.compile(
    r"(?<!\d)(?:\+?\s*91[\s\-]?)?(?:\(?0?\d{2,4}\)?[\s\-]?)\d{3,4}[\s\-]?\d{3,5}(?!\d)"
)
CC_RE = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
PIN_RE = re.compile(r"\b(?:[1-8]\d{5}|[1-8]\d{2}\s?\d{3})\b")
ADDRESS_KEYWORDS_RE = re.compile(
    r"(?i)\b(?:road|marg|street|society|apartment|flat|floor|building|tower|plot|village|"
    r"taluka|district|colony|residency|park|complex|nagar|lane|house|block|wing|office|"
    r"address|industrial area|industrial park|phase)\b"
)

FAKE_MAP = {}

def luhn_valid(value):
    digits = [int(c) for c in re.sub(r"\D", "", value)]
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0

def initialize_fake_map():
    fake = Faker("en_IN")
    fake.seed_instance(42)
    used = set()
    for name in PERSON_NAMES:
        while True:
            candidate = fake.name()
            if candidate not in used and len(candidate.split()) >= 2:
                break
        used.add(candidate)
        FAKE_MAP[("PERSON", name.lower())] = candidate
    for i, org in enumerate(COMPANY_NAMES, 1):
        FAKE_MAP[("COMPANY", org.lower())] = f"Example Organization {i:03d} Pvt. Ltd."

def fake_value(pii_type, original):
    key = (pii_type, original.lower())
    if key in FAKE_MAP:
        return FAKE_MAP[key]
    if pii_type == "EMAIL":
        local = original.split("@", 1)[0]
        value = f"redacted.{re.sub(r'[^a-z0-9]+', '.', local.lower()).strip('.')}@example.com"
    elif pii_type == "PHONE":
        value = "+91 90000 12345"
    elif pii_type == "SSN":
        value = "000-12-3456"
    elif pii_type == "CREDIT_CARD":
        value = "4111 1111 1111 1111"
    elif pii_type == "DATE_OF_BIRTH":
        value = "January 1, 1990"
    elif pii_type == "IP_ADDRESS":
        value = "192.0.2.1"
    elif pii_type == "ADDRESS":
        value = "101 Example Street, Pune, Maharashtra 411001, India"
    else:
        value = "[REDACTED]"
    FAKE_MAP[key] = value
    return value

def detect_spans(text):
    spans = []
    def add(pattern, pii_type, priority):
        for m in pattern.finditer(text):
            spans.append((m.start(), m.end(), pii_type, priority, m.group()))

    add(EMAIL_RE, "EMAIL", 100)
    add(IP_RE, "IP_ADDRESS", 100)
    add(SSN_RE, "SSN", 100)
    add(DOB_RE, "DATE_OF_BIRTH", 100)

    for m in CC_RE.finditer(text):
        if luhn_valid(m.group()):
            spans.append((m.start(), m.end(), "CREDIT_CARD", 100, m.group()))

    for m in PHONE_RE.finditer(text):
        digits = re.sub(r"\D", "", m.group())
        if len(digits) in (10, 11, 12) and (
            re.search(r"\+?\s*91", m.group()) or digits.startswith("0") or len(digits) == 10
        ):
            spans.append((m.start(), m.end(), "PHONE", 90, m.group()))

    for segment in re.finditer(r"[^;\n]+", text):
        s = segment.group()
        if PIN_RE.search(s) and ADDRESS_KEYWORDS_RE.search(s):
            spans.append((segment.start(), segment.end(), "ADDRESS", 80, s))

    for name in sorted(PERSON_NAMES, key=len, reverse=True):
        for m in re.finditer(re.escape(name), text, re.I):
            spans.append((m.start(), m.end(), "PERSON", 30, m.group()))

    for org in sorted(COMPANY_NAMES, key=len, reverse=True):
        for m in re.finditer(re.escape(org), text, re.I):
            spans.append((m.start(), m.end(), "COMPANY", 20, m.group()))

    spans.sort(key=lambda x: (-x[3], -(x[1] - x[0]), x[0]))
    chosen, occupied = [], []
    for sp in spans:
        a, b = sp[0], sp[1]
        if not any(not (b <= c or a >= d) for c, d in occupied):
            chosen.append(sp)
            occupied.append((a, b))
    return sorted(chosen, key=lambda x: x[0])

def redact_text(text):
    spans = detect_spans(text)
    if not spans:
        return text
    out, last = [], 0
    for start, end, pii_type, _, original in spans:
        out.append(text[last:start])
        out.append(fake_value(pii_type, original))
        last = end
    out.append(text[last:])
    return "".join(out)

def iter_paragraphs(container):
    for p in getattr(container, "paragraphs", []):
        yield p
    for table in getattr(container, "tables", []):
        for row in table.rows:
            for cell in row.cells:
                yield from iter_paragraphs(cell)

def redact_document(input_path, output_path):
    doc = Document(input_path)
    containers = [doc]
    for section in doc.sections:
        containers.extend([
            section.header, section.footer,
            section.first_page_header, section.first_page_footer,
            section.even_page_header, section.even_page_footer
        ])

    seen = set()
    for container in containers:
        for p in iter_paragraphs(container):
            if p._p in seen:
                continue
            seen.add(p._p)
            if not p.text:
                continue
            redacted = redact_text(p.text)
            if redacted != p.text:
                if p.runs:
                    p.runs[0].text = redacted
                    for run in p.runs[1:]:
                        run.text = ""
                else:
                    p.add_run(redacted)
    doc.save(output_path)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python redact_pii.py <input.docx> <output.docx>")
        raise SystemExit(2)
    initialize_fake_map()
    redact_document(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"Redacted document written to {sys.argv[2]}")
