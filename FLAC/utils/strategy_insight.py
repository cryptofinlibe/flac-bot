import os
import xml.etree.ElementTree as ET
from datetime import datetime

SENTIMENT_DIR = 'data/sentiment'
ONCHAIN_DIR = 'data/onchain'

def load_latest_analysis(token):
    today = datetime.now().strftime('%y%m%d')
    token = token.upper()

    def find_latest_file(folder, prefix):
        for fname in sorted(os.listdir(folder), reverse=True):
            if fname.startswith(f"{prefix}_{token}_{today}"):
                return os.path.join(folder, fname)
        if token != 'BTC':
            for fname in sorted(os.listdir(folder), reverse=True):
                if fname.startswith(f"{prefix}_BTC_{today}"):
                    return os.path.join(folder, fname)
        return None

    def read_xml_content(fpath):
        try:
            tree = ET.parse(fpath)
            root = tree.getroot()
            return root.find('content').text.strip()
        except Exception:
            return ''

    sentiment_file = find_latest_file(SENTIMENT_DIR, 'S')
    onchain_file = find_latest_file(ONCHAIN_DIR, 'O')
    
    sentiment = read_xml_content(sentiment_file) if sentiment_file else ''
    onchain = read_xml_content(onchain_file) if onchain_file else ''

    return sentiment, onchain

# Example integration
def analyze_with_sentiment(token):
    sentiment, onchain = load_latest_analysis(token)

    # Use this for decision making or logging
    if sentiment:
        print(f"🧠 Sentiment for {token}:\n{sentiment}\n")
    else:
        print(f"⚠️ No sentiment found for {token}")

    if onchain:
        print(f"🔗 Onchain for {token}:\n{onchain}\n")
    else:
        print(f"⚠️ No onchain data found for {token}")

    # Next: add logic to adjust or annotate strategy
    return {
        'sentiment': sentiment,
        'onchain': onchain
    }

# Usage: analyze_with_sentiment('ETH') or analyze_with_sentiment('PEPE')
