import win32com.client as win32
import os
import datetime
import re
from difflib import SequenceMatcher

def normalize_company_name(name):
    """
    Normalizes company names by removing common suffixes, punctuation, and converting to lowercase.
    """
    if not name:
        return ""
    
    # Lowercase
    name = name.lower()
    
    # Remove text in parentheses (e.g. ticker symbols or abbreviations)
    name = re.sub(r'\s*\(.*?\)', '', name)
    
    # Remove punctuation
    name = re.sub(r'[^\w\s]', ' ', name)
    
    # Common suffixes to remove (sorted by length to match longest first)
    suffixes = [
        'co ltd', 'co limited', 'company limited', 'limited', 'ltd', 
        'inc', 'incorporated', 'corp', 'corporation', 
        'holdings', 'group', 'company', 'plc', 'llc', 'lp',
        'international', 'technologies', 'technology', 'biotech', 'biotechnology'
    ]
    suffixes.sort(key=len, reverse=True)
    
    cleaned_name = name
    found_suffix = True
    while found_suffix:
        found_suffix = False
        cleaned_name = cleaned_name.strip()
        for suffix in suffixes:
            if cleaned_name.endswith(" " + suffix):
                cleaned_name = cleaned_name[:-(len(suffix)+1)]
                found_suffix = True
                break
            elif cleaned_name == suffix:
                # If the name is JUST the suffix (unlikely but possible), clear it
                cleaned_name = ""
                found_suffix = True
                break
                
    return cleaned_name.strip()

def are_names_similar(name1, name2, threshold=0.85):
    """
    Checks if two company names are similar using fuzzy matching and token set logic.
    """
    n1 = normalize_company_name(name1)
    n2 = normalize_company_name(name2)
    
    if not n1 or not n2:
        return False
        
    # 1. Exact match after normalization
    if n1 == n2:
        return True
        
    # 2. Token Set Similarity
    # This handles cases like "Nanjing Nuoling" vs "Nuoling"
    tokens1 = n1.split()
    tokens2 = n2.split()
    
    if not tokens1 or not tokens2:
        return False
        
    # Ensure tokens1 is the shorter one (or equal)
    if len(tokens1) > len(tokens2):
        tokens1, tokens2 = tokens2, tokens1
        
    # For each token in the shorter list, find the best match in the longer list
    scores = []
    for t1 in tokens1:
        best_token_score = 0
        for t2 in tokens2:
            score = SequenceMatcher(None, t1, t2).ratio()
            # Bonus for prefix match (e.g. bio vs biotech)
            if len(t1) > 3 and len(t2) > 3:
                if t2.startswith(t1) or t1.startswith(t2):
                    score = max(score, 0.95)
            
            if score > best_token_score:
                best_token_score = score
        scores.append(best_token_score)
        
    # Average score of the best matches for the shorter name's tokens
    final_score = sum(scores) / len(scores)
    
    return final_score >= threshold

def open_email_draft(recipient, attachment_path):
    """
    Opens an Outlook email draft with the attached report.
    """
    try:
        outlook = win32.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)
        
        mail.To = recipient
        mail.Subject = f"{datetime.datetime.now().strftime('%d %b')} HongKong IPO Analysis Report"
        mail.Body = "Please find the attached Hong Kong IPO Analysis Report."
        
        if os.path.exists(attachment_path):
            mail.Attachments.Add(attachment_path)
        else:
            print(f"Attachment not found: {attachment_path}")
            
        mail.Display(True)
        return True
    except Exception as e:
        print(f"Error opening Outlook: {e}")
        return False
