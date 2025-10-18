# Substitution rules for normalizing Tagalog spelling (if needed)
SUBSTITUTIONS = {
    'c': 'k',
    'f': 'p',
    'j': 'h',
    'q': 'k',
    'v': 'b',
    'x': 'ks',
    'z': 's'
}

# Common/important Tagalog words for typo/scrambling detection
COMMON_WORDS = {
    'babae', 'lalaki', 'tao', 'anak', 'pamilya', 'bahay', 'gulo', 'tubig',
    'araw', 'gabi', 'buwan', 'taon', 'oras', 'mabuti', 'masama', 'malaki',
    'maliit', 'kumain', 'uminom', 'matulog', 'maganda', 'pangit', 'mga',
    'ang', 'sa', 'ng', 'na', 'ay', 'at', 'para', 'hindi', 'ako', 'ka',
    'siya', 'kami', 'kayo', 'sila', 'ito', 'iyan', 'iyon'
}

# Default suggestion settings
SUGGESTION_LIMIT = 3
SCORE_CUTOFF = 70
