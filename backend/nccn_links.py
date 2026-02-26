

NCCN_LINKS = {

    'breast': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1419',
    'lung': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1450',
    'colon': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1428',
    'rectal': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1461',
    'prostate': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1455',
    'pancreatic': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1454',
    'esophageal': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1433',
    'stomach': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1434',
    'liver': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1438',
    'kidney': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1440',
    'bladder': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1417',
    'ovarian': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1453',
    'cervical': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1426',
    'uterine': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1473',
    'melanoma': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1492',
    'head_neck': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1437',
    'thyroid': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1470',
    'brain': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1421',
    'soft_tissue_sarcoma': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1465',
    'bone_sarcoma': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1418',
    'gist': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1436',
    'anal': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1414',
    'penile': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1460',
    'testicular': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1469',
    'cancer_unknown_primary': 'https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1424',
    'general': 'https://www.nccn.org/guidelines/category_1'
}

def get_nccn_link(cancer_type: str) -> str:
    """
    Возвращает ссылку на NCCN Guidelines для указанного типа рака
    """

    if cancer_type in NCCN_LINKS:
        return NCCN_LINKS[cancer_type]
    

    variations = [
        cancer_type,
        cancer_type.replace('_cancer', ''),
        cancer_type.replace('cancer', ''),
        cancer_type.replace('_', ''),
    ]
    
    for var in variations:
        if var in NCCN_LINKS:
            return NCCN_LINKS[var]

    return NCCN_LINKS.get('general', 'https://www.nccn.org/guidelines/category_1')