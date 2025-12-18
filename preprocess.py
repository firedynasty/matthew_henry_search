#!/usr/bin/env python3
"""
Preprocess Matthew Henry Commentary HTM files into a searchable JSON format.
This reduces the data size and speeds up search at runtime.
Also extracts cross-references with surrounding context.
"""

import os
import re
import json
import argparse
from html.parser import HTMLParser
from pathlib import Path

# Book codes mapping
BOOKS = {
    '00': 'Preface',
    '01': 'Genesis', '02': 'Exodus', '03': 'Leviticus', '04': 'Numbers', '05': 'Deuteronomy',
    '06': 'Joshua', '07': 'Judges', '08': 'Ruth', '09': '1 Samuel', '10': '2 Samuel',
    '11': '1 Kings', '12': '2 Kings', '13': '1 Chronicles', '14': '2 Chronicles',
    '15': 'Ezra', '16': 'Nehemiah', '17': 'Esther', '18': 'Job', '19': 'Psalms',
    '20': 'Proverbs', '21': 'Ecclesiastes', '22': 'Song of Solomon', '23': 'Isaiah',
    '24': 'Jeremiah', '25': 'Lamentations', '26': 'Ezekiel', '27': 'Daniel',
    '28': 'Hosea', '29': 'Joel', '30': 'Amos', '31': 'Obadiah', '32': 'Jonah',
    '33': 'Micah', '34': 'Nahum', '35': 'Habakkuk', '36': 'Zephaniah', '37': 'Haggai',
    '38': 'Zechariah', '39': 'Malachi',
    '40': 'Matthew', '41': 'Mark', '42': 'Luke', '43': 'John', '44': 'Acts',
    '45': 'Romans', '46': '1 Corinthians', '47': '2 Corinthians', '48': 'Galatians',
    '49': 'Ephesians', '50': 'Philippians', '51': 'Colossians', '52': '1 Thessalonians',
    '53': '2 Thessalonians', '54': '1 Timothy', '55': '2 Timothy', '56': 'Titus',
    '57': 'Philemon', '58': 'Hebrews', '59': 'James', '60': '1 Peter', '61': '2 Peter',
    '62': '1 John', '63': '2 John', '64': '3 John', '65': 'Jude', '66': 'Revelation',
}

# Mapping for passage abbreviations to full book names
PASSAGE_BOOK_MAP = {
    'ge': 'Genesis', 'gen': 'Genesis',
    'ex': 'Exodus', 'exo': 'Exodus', 'exod': 'Exodus',
    'le': 'Leviticus', 'lev': 'Leviticus',
    'nu': 'Numbers', 'num': 'Numbers',
    'de': 'Deuteronomy', 'deu': 'Deuteronomy', 'deut': 'Deuteronomy',
    'jos': 'Joshua', 'josh': 'Joshua',
    'jud': 'Judges', 'judg': 'Judges',
    'ru': 'Ruth', 'rut': 'Ruth', 'ruth': 'Ruth',
    '1sa': '1 Samuel', '1sam': '1 Samuel',
    '2sa': '2 Samuel', '2sam': '2 Samuel',
    '1ki': '1 Kings', '1kin': '1 Kings', '1kings': '1 Kings',
    '2ki': '2 Kings', '2kin': '2 Kings', '2kings': '2 Kings',
    '1ch': '1 Chronicles', '1chr': '1 Chronicles', '1chron': '1 Chronicles',
    '2ch': '2 Chronicles', '2chr': '2 Chronicles', '2chron': '2 Chronicles',
    'ezr': 'Ezra', 'ezra': 'Ezra',
    'ne': 'Nehemiah', 'neh': 'Nehemiah',
    'es': 'Esther', 'est': 'Esther', 'esth': 'Esther',
    'job': 'Job',
    'ps': 'Psalms', 'psa': 'Psalms', 'psalm': 'Psalms', 'psalms': 'Psalms',
    'pr': 'Proverbs', 'pro': 'Proverbs', 'prov': 'Proverbs',
    'ec': 'Ecclesiastes', 'ecc': 'Ecclesiastes', 'eccl': 'Ecclesiastes',
    'so': 'Song of Solomon', 'song': 'Song of Solomon', 'sos': 'Song of Solomon',
    'isa': 'Isaiah', 'is': 'Isaiah',
    'jer': 'Jeremiah', 'je': 'Jeremiah',
    'la': 'Lamentations', 'lam': 'Lamentations',
    'eze': 'Ezekiel', 'ezek': 'Ezekiel',
    'da': 'Daniel', 'dan': 'Daniel',
    'ho': 'Hosea', 'hos': 'Hosea',
    'joe': 'Joel', 'joel': 'Joel',
    'am': 'Amos', 'amo': 'Amos', 'amos': 'Amos',
    'ob': 'Obadiah', 'oba': 'Obadiah', 'obad': 'Obadiah',
    'jon': 'Jonah', 'jona': 'Jonah', 'jonah': 'Jonah',
    'mic': 'Micah', 'mi': 'Micah',
    'na': 'Nahum', 'nah': 'Nahum',
    'hab': 'Habakkuk',
    'zep': 'Zephaniah', 'zeph': 'Zephaniah',
    'hag': 'Haggai',
    'zec': 'Zechariah', 'zech': 'Zechariah',
    'mal': 'Malachi',
    'mt': 'Matthew', 'mat': 'Matthew', 'matt': 'Matthew',
    'mk': 'Mark', 'mar': 'Mark', 'mark': 'Mark',
    'lu': 'Luke', 'luk': 'Luke', 'luke': 'Luke',
    'joh': 'John', 'john': 'John', 'jn': 'John',
    'ac': 'Acts', 'act': 'Acts', 'acts': 'Acts',
    'ro': 'Romans', 'rom': 'Romans',
    '1co': '1 Corinthians', '1cor': '1 Corinthians',
    '2co': '2 Corinthians', '2cor': '2 Corinthians',
    'ga': 'Galatians', 'gal': 'Galatians',
    'eph': 'Ephesians',
    'php': 'Philippians', 'phil': 'Philippians',
    'col': 'Colossians',
    '1th': '1 Thessalonians', '1thess': '1 Thessalonians',
    '2th': '2 Thessalonians', '2thess': '2 Thessalonians',
    '1ti': '1 Timothy', '1tim': '1 Timothy',
    '2ti': '2 Timothy', '2tim': '2 Timothy',
    'tit': 'Titus', 'titus': 'Titus',
    'phm': 'Philemon', 'phile': 'Philemon', 'philem': 'Philemon',
    'heb': 'Hebrews',
    'jas': 'James', 'jam': 'James', 'james': 'James',
    '1pe': '1 Peter', '1pet': '1 Peter',
    '2pe': '2 Peter', '2pet': '2 Peter',
    '1jo': '1 John', '1joh': '1 John', '1john': '1 John',
    '2jo': '2 John', '2joh': '2 John', '2john': '2 John',
    '3jo': '3 John', '3joh': '3 John', '3john': '3 John',
    'jude': 'Jude', 'jud': 'Jude',
    're': 'Revelation', 'rev': 'Revelation',
}


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.in_script = False
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.in_script = True
        elif tag == 'style':
            self.in_style = True

    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_script = False
        elif tag == 'style':
            self.in_style = False

    def handle_data(self, data):
        if not self.in_script and not self.in_style:
            self.text_parts.append(data)

    def get_text(self):
        return ' '.join(self.text_parts)


def strip_html(html_content):
    parser = HTMLTextExtractor()
    try:
        parser.feed(html_content)
        return parser.get_text()
    except:
        text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        return text


def get_title_from_html(html_content):
    match = re.search(r'<TITLE[^>]*>(.*?)</TITLE>', html_content, re.IGNORECASE | re.DOTALL)
    if match:
        title = match.group(1).strip()
        # Clean up the title
        title = title.replace("Matthew Henry's Complete Commentary on the Whole Bible ", "")
        return title
    return "Unknown"


def get_book_code(filename):
    """Extract book code from filename like MHC01001.HTM -> 01"""
    match = re.match(r'MHC(\d{2})', filename)
    if match:
        return match.group(1)
    return '00'


def get_chapter_from_filename(filename):
    """Extract chapter number from filename like MHC19001.HTM -> 1"""
    match = re.match(r'MHC\d{2}(\d{3})\.HTM', filename, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 0


def parse_passage_ref(passage_str):
    """Parse a passage string like 'Ps+1:1-3' or 'Lu+23:51' into structured data."""
    passage_str = passage_str.replace('+', ' ').strip()

    # Match patterns like "Ps 1:1-3", "Lu 23:51", "1Co 6:2"
    match = re.match(r'(\d?\s*[A-Za-z]+)\s*(\d+):?([\d,\-]*)', passage_str)
    if not match:
        return None

    book_abbr = match.group(1).lower().replace(' ', '')
    chapter = match.group(2)
    verses = match.group(3) if match.group(3) else ''

    book_name = PASSAGE_BOOK_MAP.get(book_abbr)
    if not book_name:
        return None

    return {
        'book': book_name,
        'chapter': int(chapter),
        'verses': verses,
        'display': f"{book_name} {chapter}" + (f":{verses}" if verses else "")
    }


def extract_references_with_context(html_content, context_chars=200):
    """Extract all Bible references from HTML with surrounding context."""
    references = []

    # Pattern for Bible reference links
    pattern = r'<A\s+HREF="[^"]*passage=([^"&]+)"[^>]*>([^<]+)</A>'

    # Create plain text version for context
    text_content = strip_html(html_content)
    text_content = re.sub(r'\s+', ' ', text_content).strip()

    for match in re.finditer(pattern, html_content, re.IGNORECASE):
        passage_param = match.group(1)
        display_text = match.group(2).strip()

        parsed = parse_passage_ref(passage_param)
        if not parsed:
            continue

        # Find context around this reference
        display_clean = re.sub(r'\s+', ' ', strip_html(display_text)).strip()
        pos = text_content.find(display_clean)

        if pos != -1:
            start = max(0, pos - context_chars)
            end = min(len(text_content), pos + len(display_clean) + context_chars)

            # Extend to word boundaries
            while start > 0 and text_content[start] not in ' .\n':
                start -= 1
            while end < len(text_content) and text_content[end] not in ' .\n':
                end += 1

            context = text_content[start:end].strip()
            if start > 0:
                context = '...' + context
            if end < len(text_content):
                context = context + '...'
        else:
            context = display_text

        references.append({
            'ref': parsed,
            'display': display_text,
            'context': context
        })

    return references


def build_book_structure(htm_files):
    """Build a structure of books and their available chapters from filenames."""
    structure = {}

    for filepath in htm_files:
        book_code = get_book_code(filepath.name)
        chapter = get_chapter_from_filename(filepath.name)

        if book_code not in structure:
            structure[book_code] = {
                'name': BOOKS.get(book_code, 'Unknown'),
                'chapters': []
            }

        if chapter > 0 and chapter not in structure[book_code]['chapters']:
            structure[book_code]['chapters'].append(chapter)

    # Sort chapters for each book
    for book_code in structure:
        structure[book_code]['chapters'].sort()

    return structure


def main():
    parser = argparse.ArgumentParser(description='Preprocess Matthew Henry Commentary')
    parser.add_argument('-i', '--input', default='/Users/stanleytan/matthew_henry',
                        help='Directory containing HTM files')
    parser.add_argument('-o', '--output', default='./data/commentary.json',
                        help='Output JSON file')
    args = parser.parse_args()

    htm_files = sorted(Path(args.input).glob('MHC*.HTM'))

    documents = []
    total_refs = 0

    print(f"Processing {len(htm_files)} files...")

    # Build book/chapter structure from filenames
    book_structure = build_book_structure(htm_files)
    print(f"Found {len(book_structure)} books with chapters")

    for i, filepath in enumerate(htm_files):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()

            title = get_title_from_html(html_content)
            text = strip_html(html_content)
            text = re.sub(r'\s+', ' ', text).strip()

            book_code = get_book_code(filepath.name)
            book_name = BOOKS.get(book_code, 'Unknown')
            chapter = get_chapter_from_filename(filepath.name)

            # Extract cross-references with context
            references = extract_references_with_context(html_content)
            total_refs += len(references)

            documents.append({
                'id': filepath.name,
                'title': title,
                'book_code': book_code,
                'book': book_name,
                'chapter': chapter,
                'text': text,
                'references': references
            })

            if (i + 1) % 100 == 0:
                print(f"  Processed {i + 1}/{len(htm_files)} files...")

        except Exception as e:
            print(f"Error processing {filepath}: {e}")

    # Write main output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'books': BOOKS,
            'bookStructure': book_structure,
            'documents': documents
        }, f)

    # Calculate size
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"\nDone! Created {args.output}")
    print(f"  {len(documents)} documents")
    print(f"  {total_refs} cross-references extracted")
    print(f"  {size_mb:.1f} MB")


if __name__ == '__main__':
    main()
