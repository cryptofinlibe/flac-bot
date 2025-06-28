import os
from datetime import datetime
from xml.etree.ElementTree import ElementTree

SENTIMENT_DIR = 'data/sentiment'
ONCHAIN_DIR = 'data/onchain'

def find_latest_file(directory, token_prefix):
    token_prefix = token_prefix.upper()
    files = [f for f in os.listdir(directory) if f.startswith(token_prefix)]
    if not files:
        return None
    files.sort(reverse=True)
    return os.path.join(directory, files[0])

def read_xml_content(filepath):
    try:
        tree = ElementTree()
        tree.parse(filepath)
        root = tree.getroot()
        return root.find('content').text if root.find('content') is not None else ''
    except Exception as e:
        return f"❌ Failed to read {filepath}: {e}"

def load_latest_analysis(token):
    token = token.upper()
    sentiment_file = find_latest_file(SENTIMENT_DIR, f'S_{token}') or find_latest_file(SENTIMENT_DIR, 'S_BTC')
    onchain_file = find_latest_file(ONCHAIN_DIR, f'O_{token}') or find_latest_file(ONCHAIN_DIR, 'O_BTC')

    sentiment_text = read_xml_content(sentiment_file) if sentiment_file else '⚠️ No sentiment data found.'
    onchain_text = read_xml_content(onchain_file) if onchain_file else '⚠️ No on-chain data found.'

    return {
        'sentiment': sentiment_text,
        'onchain': onchain_text,
        'sentiment_file': sentiment_file,
        'onchain_file': onchain_file
    }

def analyze_with_sentiment(token):
    analysis = load_latest_analysis(token)
    print(f"🔍 Sentiment Insight ({token}):\n{analysis['sentiment']}")
    print(f"🔗 On-Chain Insight ({token}):\n{analysis['onchain']}")
    return analysis
