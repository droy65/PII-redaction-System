import re
import sys
from pathlib import Path
from collections import Counter

from docx import Document
from faker import Faker


# Regular expressions for structured PII
EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

PHONE_RE = re.compile(
    r"(?<!\d)(?:\+91[\s-]?)?(?:\d{10}|\d{5}[\s-]\d{5})(?!\d)"
)

IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

SSN_RE = re.compile(r"\b\d{3}[- ]\d{2}[- ]\d{4}\b")

CARD_RE = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")

DOB_RE = re.compile(
    r"(?i)\b(?:date of birth|dob)\s*[:\-]?\s*"
    r"(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
    r"|[A-Za-z]+\s+\d{1,2},?\s+\d{4})"
)

PIN_RE = re.compile(r"\b[1-8]\d{5}\b")

ADDRESS_WORDS_RE = re.compile(
    r"(?i)\b(road|street|society|apartment|flat|floor|"
    r"building|tower|plot|village|district|colony|park|"
    r"complex|nagar|lane|house|block|office|address|"
    r"industrial area|industrial park|phase)\b"
)


# Names found while reviewing the supplied prospectus.
PERSON_NAMES = [
    "Sarthak Malvadkar",
    "Kushal Subbayya Hegde",
    "Pushpa Kushal Hegde",
    "Rajesh Kushal Hegde",
    "Rohit Kushal Hegde",
    "Rakhi Girija Shetty",
    "Maithili Rajesh Hegde",
    "Katyayani Balasubramanian",
    "Rupal K. Sancheti",
    "Salil Ajay Bhargava",
    "Jabeen Ajay Menon",
    "Ajay Menon",
    "Sunil Nagayya Shetty",
    "Dinesh Hirachand Munot",
    "Ajay Shriram Patil",
    "Ram Kumar Tiwari",
    "Indu Jacob",
    "Lokesh Shah",
    "Soumavo Sarkar",
    "Kishan Rastogi",
    "Abhijit Diwan",
    "Prakash Boricha",
    "Shanti Gopalkrishnan",
    "Eric Bacha",
    "Sachin Gawade",
    "Pravin Teli",
    "Siddharth Jadhav",
    "Tushar Gavankar",
    "Varun Badai",
    "Hitesh Ramani",
    "Chitra Raste",
    "Sharmila Joshi",
    "Cherag Gyara",
    "Manisha Shukla",
    "Tushar Wakhele",
    "Ashish Mathew Pulloor",
    "Anand Soni",
    "Parag Pansare",
    "Sangeeta Ramprasad Rai",
    "Jayaram Shetty",
    "Karunakar Bhandary",
    "Karunakar Hegde",
    "Narayana B. Shetty",
    "Vijay Hegde",
    "DM Shetty",
    "Gopal BO",
    "SA Shetty",
]


# Organizations found while reviewing the supplied prospectus.
COMPANY_NAMES = [
    "KSH International Limited",
    "KSH International Private Limited",
    "Bhandary Metal Extrusion Private Limited",
    "Nuvama Wealth Management Limited",
    "ICICI Securities Limited",
    "MUFG Intime India Private Limited",
    "Link Intime India Private Limited",
    "Trilegal",
    "HDFC Bank Limited",
    "ICICI Bank Limited",
    "ICICI Bank",
    "Kirtane & Pandit LLP",
    "Export-Import Bank of India",
    "IndusInd Bank Limited",
    "State Bank of India",
    "The Federal Bank Limited",
    "Bajaj Finance Limited",
    "Bajaj Finserv",
    "CARE Ratings Limited",
    "National Securities Depository Limited",
    "National Payments Corporation of India",
    "Reserve Bank of India",
    "BSE Limited",
    "National Stock Exchange of India Limited",
    "Nuvama",
    "ICICI Securities",
    "Waterloo Industrial Park VI Private Limited",
    "Waterloo Motors Private Limited",
    "KSH Project Management Services Private Limited",
    "KSH Infra Park 5 Private Limited",
    "KSH Infra Park VI Private Limited",
    "KSH Distriparks Private Limited",
    "KSH Integrated Logistics Private Limited",
    "Kushal Motors and Electricals Private Limited",
    "Nidec Industrial Automation India Private Limited",
    "Precision Wires India Limited",
    "Bharat Bijlee Limited",
    "Elantas Beck India Limited",
    "Hindalco Industries Limited",
    "Vedanta Limited",
    "Solar Energy Corporation of India",
    "Kushal Electricals",
    "Waterloo Motors",
]


fake = Faker("en_IN")
fake.seed_instance(42)

# Keeps replacements consistent throughout the document.
replacements = {}
replacement_counts = Counter()


def valid_credit_card(value):
    """Check a possible card number using the Luhn algorithm."""
    digits = re.sub(r"\D", "", value)

    if not 13 <= len(digits) <= 19:
        return False

    total = 0

    for index, digit in enumerate(reversed(digits)):
        number = int(digit)

        if index % 2 == 1:
            number *= 2
            if number > 9:
                number -= 9

        total += number

    return total % 10 == 0


def get_fake_value(pii_type, original):
    """Return the same fake value whenever the same PII appears again."""
    key = (pii_type, original.lower())

    if key in replacements:
        return replacements[key]

    if pii_type == "PERSON":
        value = fake.name()
    elif pii_type == "EMAIL":
        value = f"person{len(replacements) + 1}@example.com"
    elif pii_type == "PHONE":
        value = "+91 90000 12345"
    elif pii_type == "COMPANY":
        value = "Example Organization Pvt. Ltd."
    elif pii_type == "ADDRESS":
        value = "101 Example Street, Pune, Maharashtra 411001"
    elif pii_type == "SSN":
        value = "000-12-3456"
    elif pii_type == "CREDIT_CARD":
        value = "4111 1111 1111 1111"
    elif pii_type == "DATE_OF_BIRTH":
        value = "January 1, 1990"
    elif pii_type == "IP_ADDRESS":
        value = "192.0.2.1"
    else:
        value = "[REDACTED]"

    replacements[key] = value
    return value


def find_pii(text):
    """Find PII in a paragraph using rules and reviewed entities."""
    matches = []

    def add_matches(pattern, pii_type):
        for match in pattern.finditer(text):
            matches.append(
                (match.start(), match.end(), pii_type, match.group())
            )

    add_matches(EMAIL_RE, "EMAIL")
    add_matches(PHONE_RE, "PHONE")
    add_matches(IP_RE, "IP_ADDRESS")
    add_matches(SSN_RE, "SSN")
    add_matches(DOB_RE, "DATE_OF_BIRTH")

    # A long number is treated as a card only if it passes Luhn.
    for match in CARD_RE.finditer(text):
        if valid_credit_card(match.group()):
            matches.append(
                (match.start(), match.end(), "CREDIT_CARD", match.group())
            )

    # Address rule: an Indian PIN code plus an address-related word.
    for match in re.finditer(r"[^;\n]+", text):
        part = match.group()

        if PIN_RE.search(part) and ADDRESS_WORDS_RE.search(part):
            matches.append(
                (match.start(), match.end(), "ADDRESS", part)
            )

    # Names from the reviewed prospectus.
    for name in PERSON_NAMES:
        pattern = re.compile(re.escape(name), re.IGNORECASE)

        for match in pattern.finditer(text):
            matches.append(
                (match.start(), match.end(), "PERSON", match.group())
            )

    # Companies from the reviewed prospectus.
    for company in COMPANY_NAMES:
        pattern = re.compile(re.escape(company), re.IGNORECASE)

        for match in pattern.finditer(text):
            matches.append(
                (match.start(), match.end(), "COMPANY", match.group())
            )

    # If matches overlap, keep the longer match.
    matches.sort(key=lambda item: (item[0], -(item[1] - item[0])))

    selected = []
    last_end = -1

    for match in matches:
        if match[0] >= last_end:
            selected.append(match)
            last_end = match[1]

    return selected


def redact_text(text):
    """Replace all PII found in one paragraph."""
    matches = find_pii(text)

    if not matches:
        return text

    pieces = []
    position = 0

    for start, end, pii_type, original in matches:
        pieces.append(text[position:start])

        fake_value = get_fake_value(pii_type, original)
        pieces.append(fake_value)

        replacement_counts[pii_type] += 1
        position = end

    pieces.append(text[position:])

    return "".join(pieces)


def iter_paragraphs(container):
    """Yield paragraphs, including paragraphs inside tables."""
    for paragraph in getattr(container, "paragraphs", []):
        yield paragraph

    for table in getattr(container, "tables", []):
        for row in table.rows:
            for cell in row.cells:
                yield from iter_paragraphs(cell)


def process_document(input_file, output_file):
    """Read, redact and save the DOCX document."""
    document = Document(input_file)

    containers = [document]

    # Headers and footers can also contain PII.
    for section in document.sections:
        containers.extend([
            section.header,
            section.footer,
            section.first_page_header,
            section.first_page_footer,
            section.even_page_header,
            section.even_page_footer,
        ])

    processed_paragraphs = set()

    for container in containers:
        for paragraph in iter_paragraphs(container):

            if paragraph._p in processed_paragraphs:
                continue

            processed_paragraphs.add(paragraph._p)

            if not paragraph.text:
                continue

            old_text = paragraph.text
            new_text = redact_text(old_text)

            if new_text == old_text:
                continue

            # Keep the paragraph and replace its text.
            if paragraph.runs:
                paragraph.runs[0].text = new_text

                for run in paragraph.runs[1:]:
                    run.text = ""
            else:
                paragraph.add_run(new_text)

    document.save(output_file)


def main():
    if len(sys.argv) != 3:
        print("Usage: python redact_pii.py input.docx output.docx")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])

    if not input_file.exists():
        print(f"Input file not found: {input_file}")
        sys.exit(1)

    process_document(input_file, output_file)

    print("PII redaction completed.")
    print(f"Saved redacted document to: {output_file}")

    if replacement_counts:
        print("\nPII detected:")
        for pii_type, count in replacement_counts.items():
            print(f"  {pii_type}: {count}")


if __name__ == "__main__":
    main()
