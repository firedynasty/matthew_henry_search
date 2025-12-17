#!/usr/bin/env python3
"""
Preprocess Matthew Henry Commentary HTM files into a searchable JSON format.
This reduces the data size and speeds up search at runtime.
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


def main():
    parser = argparse.ArgumentParser(description='Preprocess Matthew Henry Commentary')
    parser.add_argument('-i', '--input', default='/Users/stanleytan/matthew_henry',
                        help='Directory containing HTM files')
    parser.add_argument('-o', '--output', default='./data/commentary.json',
                        help='Output JSON file')
    args = parser.parse_args()

    htm_files = sorted(Path(args.input).glob('MHC*.HTM'))

    documents = []

    print(f"Processing {len(htm_files)} files...")

    for i, filepath in enumerate(htm_files):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()

            title = get_title_from_html(html_content)
            text = strip_html(html_content)
            # Normalize whitespace
            text = re.sub(r'\s+', ' ', text).strip()

            book_code = get_book_code(filepath.name)
            book_name = BOOKS.get(book_code, 'Unknown')

            documents.append({
                'id': filepath.name,
                'title': title,
                'book_code': book_code,
                'book': book_name,
                'text': text
            })

            if (i + 1) % 100 == 0:
                print(f"  Processed {i + 1}/{len(htm_files)} files...")

        except Exception as e:
            print(f"Error processing {filepath}: {e}")

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'books': BOOKS,
            'documents': documents
        }, f)

    # Calculate size
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"\nDone! Created {args.output}")
    print(f"  {len(documents)} documents")
    print(f"  {size_mb:.1f} MB")


if __name__ == '__main__':
    main()
