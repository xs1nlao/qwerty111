

ESMO_LINKS = {

    'breast': 'https://www.esmo.org/guidelines/breast-cancer',
    'lung': 'https://www.esmo.org/guidelines/lung-and-chest-tumours',
    'colon': 'https://www.esmo.org/guidelines/gastrointestinal-cancers',
    'rectal': 'https://www.esmo.org/guidelines/gastrointestinal-cancers',
    'prostate': 'https://www.esmo.org/guidelines/genitourinary-cancers',
    'pancreatic': 'https://www.esmo.org/guidelines/gastrointestinal-cancers',
    'esophageal': 'https://www.esmo.org/guidelines/gastrointestinal-cancers',
    'stomach': 'https://www.esmo.org/guidelines/gastrointestinal-cancers',
    'liver': 'https://www.esmo.org/guidelines/gastrointestinal-cancers',
    'kidney': 'https://www.esmo.org/guidelines/genitourinary-cancers',
    'bladder': 'https://www.esmo.org/guidelines/genitourinary-cancers',
    'ovarian': 'https://www.esmo.org/guidelines/gynaecological-cancers',
    'cervical': 'https://www.esmo.org/guidelines/gynaecological-cancers',
    'uterine': 'https://www.esmo.org/guidelines/gynaecological-cancers',
    'melanoma': 'https://www.esmo.org/guidelines/melanoma',
    'head_neck': 'https://www.esmo.org/guidelines/head-and-neck-cancers',
    'thyroid': 'https://www.esmo.org/guidelines/endocrine-and-neuroendocrine-cancers',
    'brain': 'https://www.esmo.org/guidelines/neuro-oncology',
    'soft_tissue_sarcoma': 'https://www.esmo.org/guidelines/sarcoma',
    'bone_sarcoma': 'https://www.esmo.org/guidelines/sarcoma',
    'gist': 'https://www.esmo.org/guidelines/gastrointestinal-cancers',
    'anal': 'https://www.esmo.org/guidelines/gastrointestinal-cancers',
    'testicular': 'https://www.esmo.org/guidelines/genitourinary-cancers',
    'cancer_unknown_primary': 'https://www.esmo.org/guidelines/guidelines-by-topic/esmo-clinical-practice-gguidelines-cancer-of-unknown-primary',
    'general': 'https://www.esmo.org/guidelines'
}

def get_esmo_link(cancer_type: str) -> str:
    """
    Возвращает ссылку на ESMO Guidelines для указанного типа рака
    """

    if cancer_type in ESMO_LINKS:
        return ESMO_LINKS[cancer_type]
    

    variations = [
        cancer_type,
        cancer_type.replace('_cancer', ''),
        cancer_type.replace('cancer', ''),
        cancer_type.replace('_', ''),
    ]
    
    for var in variations:
        if var in ESMO_LINKS:
            return ESMO_LINKS[var]
    

    return ESMO_LINKS.get('general', 'https://www.esmo.org/guidelines')