EVENT_PATTERNS = {

    "earnings": {
        "required_keywords": [
            "financial results"
        ],

        "optional_keywords": [
            "revenue",
            "ebitda",
            "profit after tax",
            "net profit",
            "eps"
        ],

        "negative_keywords": [],

        "importance": 9,
        "tradeability": 8,
        "sentiment": "positive"
    },

    "open_offer": {
        "required_keywords": [
            "open offer"
        ],

        "optional_keywords": [
            "acquirer",
            "takeovers regulations",
            "expanded voting share capital",
            "offer price",
            "public shareholders"
        ],

        "negative_keywords": [],

        "importance": 10,
        "tradeability": 10,
        "sentiment": "positive"
    },

    "rights_issue": {
    "required_keywords": [
        "rights issue"
    ],

    "optional_keywords": [
        "rights entitlement",
        "issue price",
        "entitlement ratio",
        "renunciation"
    ],

    "minimum_optional_matches": 1,

    "negative_keywords": [
        "open offer"
    ],

    "importance": 8,
    "tradeability": 9,
    "sentiment": "negative"
    },

    "bonus": {
    "required_keywords": [
        "bonus shares",
        "bonus issue"
    ],

    "optional_keywords": [
        "bonus ratio",
        "equity bonus share",
        "free reserves",
        "record date"
    ],

    "negative_keywords": [],

    "importance": 7,
    "tradeability": 8,
    "sentiment": "positive"
    },

    "debt_restructuring": {
        "required_keywords": [
            "debt restructuring"
        ],

        "optional_keywords": [
            "narcl",
            "one time settlement",
            "lenders",
            "nclt",
            "insolvency"
        ],

        "negative_keywords": [],

        "importance": 10,
        "tradeability": 10,
        "sentiment": "mixed"
    },

    "order_win": {
    "required_keywords": [
        "award of contract",
        "letter of award",
        "loa",
        "lac",
        "received contract",
        "bagged order",
        "secured order",
        "work order",
        "project management consultancy",
        "execution contract",
        "purchase order",
        "order worth",
        "annual maintenance contract",
        "amc",
        "received purchase order"
    ],

    "optional_keywords": [
        "contract",
        "awarded",
        "railtel",
        "nmdc",
        "government order",
        "project"
    ],

    "negative_keywords": [
        "share purchase agreement",
        "open offer"
    ],

    "importance": 8,
    "tradeability": 9,
    "sentiment": "positive"
}
}