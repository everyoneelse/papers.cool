#!/usr/bin/env python3
"""
PubMed RSS Feed Parser

This script parses a PubMed RSS feed XML file and extracts paper information
including titles, authors, abstracts, journals, publication dates, and identifiers.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import json
import re
from typing import List, Dict, Optional
import html


class PubMedParser:
    """Parser for PubMed RSS feed XML files"""

    def __init__(self, xml_file_path: str):
        """Initialize parser with XML file path"""
        self.xml_file_path = xml_file_path
        self.namespaces = {
            'dc': 'http://purl.org/dc/elements/1.1/ ',
            'content': 'http://purl.org/rss/1.0/modules/content/ '
        }

    def parse(self) -> List[Dict]:
        """Parse the XML file and return list of paper dictionaries"""
        try:
            # Parse XML file
            tree = ET.parse(self.xml_file_path)
            root = tree.getroot()

            # Extract channel information
            channel = root.find('channel')
            if channel is None:
                raise ValueError("No channel element found in RSS feed")

            # Parse all items
            papers = []
            for item in channel.findall('item'):
                paper = self._parse_item(item)
                if paper:
                    papers.append(paper)

            return papers

        except ET.ParseError as e:
            raise ValueError(f"Failed to parse XML file: {e}")
        except FileNotFoundError:
            raise FileNotFoundError(f"XML file not found: {self.xml_file_path}")

    def _parse_item(self, item: ET.Element) -> Optional[Dict]:
        """Parse a single item element into a paper dictionary"""
        try:
            # Extract basic information
            title = self._get_text(item, 'title')
            link = self._get_text(item, 'link')
            description = self._get_text(item, 'description')
            guid = self._get_text(item, 'guid')
            pub_date = self._get_text(item, 'pubDate')

            # Extract Dublin Core metadata
            authors = self._get_authors(item)
            dc_date = self._get_text(item, 'dc:date', self.namespaces)
            dc_source = self._get_text(item, 'dc:source', self.namespaces)
            dc_title = self._get_text(item, 'dc:title', self.namespaces)

            # Extract identifiers
            identifiers = self._get_identifiers(item)

            # Extract abstract from content:encoded
            abstract = self._extract_abstract_from_content(item)

            # Create paper dictionary
            paper = {
                'title': title or dc_title,
                'authors': authors,
                'abstract': abstract or description,
                'journal': dc_source,
                'publication_date': dc_date or pub_date,
                'pmid': identifiers.get('pmid'),
                'doi': identifiers.get('doi'),
                'pmc': identifiers.get('pmc'),
                'pubmed_link': link,
                'guid': guid
            }

            return paper

        except Exception as e:
            print(f"Warning: Failed to parse item: {e}")
            return None

    def _get_text(self, element: ET.Element, tag: str, namespaces: Dict = None) -> Optional[str]:
        """Safely extract text content from an XML element"""
        found = element.find(tag, namespaces or {})
        return found.text.strip() if found is not None and found.text else None

    def _get_authors(self, item: ET.Element) -> List[str]:
        """Extract all authors from dc:creator elements"""
        authors = []
        for creator in item.findall('dc:creator', self.namespaces):
            if creator.text:
                authors.append(creator.text.strip())
        return authors

    def _get_identifiers(self, item: ET.Element) -> Dict[str, str]:
        """Extract identifiers like PMID, DOI, PMC from dc:identifier elements"""
        identifiers = {}
        for identifier in item.findall('dc:identifier', self.namespaces):
            if identifier.text:
                text = identifier.text.strip().lower()
                if text.startswith('pmid:'):
                    identifiers['pmid'] = text.replace('pmid:', '')
                elif text.startswith('doi:'):
                    identifiers['doi'] = text.replace('doi:', '')
                elif text.startswith('pmc:'):
                    identifiers['pmc'] = text.replace('pmc:', '')
        return identifiers

    def _extract_abstract_from_content(self, item: ET.Element) -> Optional[str]:
        """Extract abstract text from content:encoded CDATA section"""
        content_encoded = item.find('content:encoded', self.namespaces)
        if content_encoded is not None and content_encoded.text:
            # Parse the HTML content
            html_content = content_encoded.text

            # Try to extract abstract from HTML
            # Look for <p><b>ABSTRACT</b></p> followed by all paragraphs until the next major section
            abstract_match = re.search(
                r'<p[^>]*><b>ABSTRACT</b></p>(.*?)(?=<p[^>]*style="color:\s*lightgray|<div|<p[^>]*><b>[^<]*</b></p>)',
                html_content,
                re.DOTALL | re.IGNORECASE
            )

            if abstract_match:
                abstract_html = abstract_match.group(1)
                # Convert HTML entities and remove tags, but preserve paragraph breaks
                abstract_text = re.sub(r'<[^>]+>', '', html.unescape(abstract_html))
                # Clean up extra whitespace
                abstract_text = re.sub(r'\n\s*\n', '\n\n', abstract_text.strip())
                return abstract_text.strip()

        return None

    def save_to_json(self, papers: List[Dict], output_file: str):
        """Save parsed papers to JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(papers, f, indent=2, ensure_ascii=False)

    def save_to_csv(self, papers: List[Dict], output_file: str):
        """Save parsed papers to CSV file"""
        import csv

        if not papers:
            return

        # Get all possible keys
        fieldnames = set()
        for paper in papers:
            fieldnames.update(paper.keys())

        fieldnames = sorted(fieldnames)

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(papers)

    def print_summary(self, papers: List[Dict]):
        """Print a summary of parsed papers"""
        print(f"Total papers parsed: {len(papers)}")
        print("\nFirst few papers:")
        for i, paper in enumerate(papers[:3]):
            print(f"\n{i+1}. {paper.get('title', 'No title')}")
            authors = paper.get('authors', [])
            if authors:
                print(f"   Authors: {', '.join(authors[:3])}{'...' if len(authors) > 3 else ''}")
            if paper.get('journal'):
                print(f"   Journal: {paper.get('journal')}")
            if paper.get('publication_date'):
                print(f"   Date: {paper.get('publication_date')}")
            if paper.get('pmid'):
                print(f"   PMID: {paper.get('pmid')}")
            if paper.get('doi'):
                print(f"   DOI: {paper.get('doi')}")


def main():
    """Main function to demonstrate usage"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pubmed_parser.py <xml_file_path> [output_format]")
        print("Output formats: json, csv, or both (default: json)")
        sys.exit(1)

    xml_file = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else 'json'

    # Create parser
    parser = PubMedParser(xml_file)

    try:
        # Parse papers
        papers = parser.parse()

        # Print summary
        parser.print_summary(papers)

        # Save to file(s)
        base_name = xml_file.rsplit('.', 1)[0]

        if output_format in ['json', 'both']:
            json_file = f"{base_name}_parsed.json"
            parser.save_to_json(papers, json_file)
            print(f"\nSaved {len(papers)} papers to {json_file}")

        if output_format in ['csv', 'both']:
            csv_file = f"{base_name}_parsed.csv"
            parser.save_to_csv(papers, csv_file)
            print(f"Saved {len(papers)} papers to {csv_file}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
