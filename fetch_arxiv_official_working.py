#!/usr/bin/env python3
"""
WORKING version: Fetch arXiv official results
"""

import requests
import re
import json
from datetime import datetime

def fetch_arxiv_official(date, category, keywords=None):
    """
    WORKING fetch function - using list view which is reliable
    """
    print("="*80)
    print(f"📡 FETCHING FROM arXiv OFFICIAL: {category} on {date}")
    if keywords:
        print(f"Keywords: '{keywords}'")
    print("="*80)
    
    # Use the pastweek list which works reliably
    url = f"https://arxiv.org/list/{category}/pastweek"
    print(f"\n🔗 URL: {url}")
    
    try:
        print("\n⏳ Fetching...")
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        content = response.text
        print(f"✅ Response received: {len(content)} characters")
        
        # Parse papers - look for the structure around line 180+
        # arXiv IDs: arXiv:2511.21678 etc.
        papers = []
        
        # Find all paper blocks - look for the pattern around arXiv IDs
        # Each paper has: <dt>...</dt><dd>...</dd>
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        dts = soup.find_all('dt')
        dds = soup.find_all('dd')
        
        print(f"Found {len(dts)} dt elements and {len(dds)} dd elements")
        
        if len(dts) != len(dds):
            print("❌ Mismatch between dt and dd counts")
            return []
        
        papers = []
        matched_count = 0
        
        for i, (dt, dd) in enumerate(zip(dts, dds)):
            try:
                # Extract ID from dt
                abs_link = dt.find('a', href=lambda href: href and '/abs/' in href)
                if not abs_link:
                    continue
                    
                arxiv_id = abs_link.text.replace('arXiv:', '').strip()
                
                # Extract title from dd
                title_div = dd.find('div', class_='list-title')
                if not title_div:
                    continue
                
                # Get title text (remove "Title:")
                title_text = title_div.get_text().strip()
                title = re.sub(r'^\s*Title:\s*', '', title_text, flags=re.IGNORECASE).strip()
                
                if not title:
                    continue
                
                # Skip if doesn't match keywords
                if keywords:
                    keywords_lower = keywords.lower()
                    if keywords_lower not in title.lower():
                        continue
                
                # Extract authors
                authors = []
                author_div = dd.find('div', class_='list-authors')
                if author_div:
                    author_text = author_div.get_text().strip()
                    author_text = re.sub(r'^\s*Authors:\s*', '', author_text, flags=re.IGNORECASE).strip()
                    # Extract author names (they're in <a> tags)
                    author_links = author_div.find_all('a')
                    for link in author_links:
                        name = link.get_text().strip()
                        if name and name not in authors:
                            authors.append(name)
                
                # Extract abstract
                abstract = "No Abstract"
                abstract_p = dd.find('p', class_='mathjax')
                if abstract_p:
                    abstract = abstract_p.get_text().strip()
                
                # Check date (we can't easily get submission date from list view)
                # So we'll include all and filter by keywords
                
                papers.append({
                    'arxiv_id': arxiv_id,
                    'title': title,
                    'authors': authors,
                    'abstract': abstract,
                    'categories': [category],
                    'published_date': date,  # Note: this is the target date, not actual submission date
                })
                
                matched_count += 1
                
                if matched_count <= 5:
                    print(f"\n[{matched_count}] {arxiv_id}")
                    print(f"    Title: {title[:80]}...")
                    print(f"    Authors: {', '.join(authors[:3])}")
                    
            except Exception as e:
                print(f"  Error parsing item {i}: {e}")
                continue
        
        print(f"\n✅ SUCCESSFULLY PARSED {len(papers)} PAPERS")
        print(f"   (with keywords filter: {len(papers)} matched)")
        
        return papers
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return []

def save_results(papers, date, category, keywords):
    """Save results to JSON"""
    import os
    
    output_dir = f"/home/hy/project/papers.cool/verification_results"
    os.makedirs(output_dir, exist_ok=True)
    
    kw_part = f"_keywords_{keywords.replace(' ', '_')}" if keywords else ""
    filename = f"official_results_{category}_{date}{kw_part}.json"
    filepath = os.path.join(output_dir, filename)
    
    data = {
        'metadata': {
            'fetch_date': datetime.now().isoformat(),
            'target_date': date,
            'category': category,
            'keywords': keywords,
            'total_papers': len(papers),
            'source': 'arXiv_official_website',
        },
        'papers': papers
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved to: {filepath}")
    return filepath

def main():
    # Configuration
    DATE = "2025-11-26"  # Yesterday (more likely to have papers)
    CATEGORY = "cs.AI"
    KEYWORDS = "large language model"  # Set to None for all papers
    
    # Fetch results
    papers = fetch_arxiv_official(DATE, CATEGORY, KEYWORDS)
    
    if papers:
        save_results(papers, DATE, CATEGORY, KEYWORDS)
        print(f"\n📊 SUMMARY:")
        print(f"   Date: {DATE}")
        print(f"   Category: {CATEGORY}")
        if KEYWORDS:
            print(f"   Keywords: '{KEYWORDS}'")
        print(f"   Papers: {len(papers)}")
        
        # Show next steps
        print(f"\n📝 YOUR TURN:")
        print(f"   1. Load: /home/hy/project/papers.cool/verification_results/official_results_{CATEGORY}_{DATE}_keywords_{KEYWORDS.replace(' ', '_')}.json")
        print(f"   2. Run your local search for same parameters")
        print(f"   3. Compare with official results")
        print(f"\n   Python code for you:")
        print(f'   ```python')
        print(f'   import json')
        print(f'   filepath = "/home/hy/project/papers.cool/verification_results/official_results_{CATEGORY}_{DATE}_keywords_large_language_model.json"')
        print(f'   with open(filepath, "r") as f:')
        print(f'       official_data = json.load(f)')
        print(f'   official_papers = official_data["papers"]')
        print(f'   # Now run: your_local_search("{DATE}", "{CATEGORY}", "{KEYWORDS}")')
        print(f'   # And compare!')
        print(f'   ```')
    else:
        print(f"\n❌ No papers found")
        print(f"Try: DATE='2025-11-24', KEYWORDS=None")

if __name__ == "__main__":
    main()
