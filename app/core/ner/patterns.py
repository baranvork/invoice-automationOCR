# Pattern tanımlamaları
AMOUNT_PATTERNS = {
    'subtotal': [
        r'(?:Sub|Subtotal)\s*(?:Total)?\s*(?:\(RM\))?\s*:?\s*(\d+[\d,.]+)',
        r'\(Excluded\s*GST\)\s*Sub\s*(\d+[\d,.]+)',
        r'(?:Item|Qty)\s*\(\s*s\s*\)\s*:?\s*(\d+[\d,.]+)',
    ],
    'taxes': [
        r'(?:GST|Tax)\s*(?:Amount)?\s*(?:\(RM\))?\s*:?\s*(\d+[\d,.]+)',
        r'Total\s*GST\s*(?:\(RM\))?\s*:?\s*(\d+[\d,.]+)',
        r'SR\s*\d*\s*(\d+[\d,.]+)\s*\d+[\d,.]+',  # GST summary pattern
    ],
    'total': [
        r'Total\s*(?:\(RM\))?\s*:?\s*(\d+[\d,.]+)',
        r'CASH\s*:?\s*(\d+[\d,.]+)',
        r'Total\s*Rounded\s*:?\s*(\d+[\d,.]+)',
    ]
}

ADDRESS_PATTERNS = [
    # Şirket adresi
    r'(?:NO\.?\s*\d+[^,\n]+(?:JALAN|ROAD|STREET)[^,\n]+)',
    r'BANDAR\s+BARU\s+[^,\n]+',
    r'\d{5}\s+[^,\n]+',
    # İletişim bilgileri
    r'TEL\s*:\s*[\d\-]+',
    r'FAX\s*:\s*[\d\-]+',
    r'GST\s*NO\s*:?\s*[\d\-]+',
]

COMPANY_PATTERNS = [
    # Şirket adı
    r'PERNIAGAAN\s+([A-Z\s]+HUI)',
    r'([A-Z]+\s+ENGINEERING\s+(?:SDN\s*BHD|COMPANY))',
    # Başlık kısmındaki şirket adı
    r'^([A-Z][A-Z\s]+)(?=\n)',
]

DATE_PATTERNS = {
    'invoice_date': [
        r'Date\s*:\s*(\d{1,2}/\d{1,2}/\d{4})',
        r'Date\s*:\s*(\d{1,2}-\d{1,2}-\d{4})',
    ]
}

COMPANY_KEYWORDS = [
    "sdn bhd", "enterprise", "marketing", "company", "inc", "ltd",
    "corporation", "limited", "solutions"
] 