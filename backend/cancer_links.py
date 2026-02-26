

CANCER_LINKS = {

    'breast': 'https://cr.minzdrav.gov.ru/view-cr/379_4',
    'lung': 'https://cr.minzdrav.gov.ru/view-cr/30_5',
    'colon': 'https://cr.minzdrav.gov.ru/view-cr/396_4',
    'rectal': 'https://cr.minzdrav.gov.ru/view-cr/554_4',
    'prostate': 'https://cr.minzdrav.gov.ru/view-cr/12_3',
    'stomach': 'https://cr.minzdrav.gov.ru/view-cr/574_1',
    'esophageal': 'https://cr.minzdrav.gov.ru/view-cr/237_6',
    'pancreatic': 'https://cr.minzdrav.gov.ru/view-cr/355_5',
    'kidney': 'https://cr.minzdrav.gov.ru/view-cr/526_2',
    'bladder': 'https://cr.minzdrav.gov.ru/view-cr/11_3',
    'liver': 'https://cr.minzdrav.gov.ru/view-cr/1_4',
    'melanoma': 'https://cr.minzdrav.gov.ru/view-cr/921_1',
    'cervical': 'https://cr.minzdrav.gov.ru/view-cr/344_2',
    'ovarian': 'https://cr.minzdrav.gov.ru/view-cr/547_3',
    'thyroid': 'https://cr.minzdrav.gov.ru/view-cr/329_2',
    'gist': 'https://cr.minzdrav.gov.ru/view-cr/551_3',
    'soft_tissue_sarcoma': 'https://cr.minzdrav.gov.ru/view-cr/515_3',
    'bone_sarcoma': 'https://cr.minzdrav.gov.ru/view-cr/532_5',
    'head_neck': 'https://cr.minzdrav.gov.ru/view-cr/537_3',
    'brain': 'https://cr.minzdrav.gov.ru/view-cr/585_2',
    'anal': 'https://cr.minzdrav.gov.ru/view-cr/555_3',
    'penile': 'https://cr.minzdrav.gov.ru/view-cr/51_2',
    'testicular': 'https://cr.minzdrav.gov.ru/view-cr/584_2',
    'adrenal': 'https://cr.minzdrav.gov.ru/view-cr/341_2',
    'biliary': 'https://cr.minzdrav.gov.ru/view-cr/495_2',
    'uterine': 'https://cr.minzdrav.gov.ru/view-cr/460_4',
    'cancer_unknown_primary': 'https://cr.minzdrav.gov.ru/view-cr/893_1',
    'mesothelioma': 'https://cr.minzdrav.gov.ru/view-cr/497_2',
    'neuroendocrine': 'https://cr.minzdrav.gov.ru/view-cr/610_2',
    'tracheal': 'https://cr.minzdrav.gov.ru/view-cr/330_2',
    'salivary_glands': 'https://cr.minzdrav.gov.ru/view-cr/116_2',
    'oral_cavity': 'https://cr.minzdrav.gov.ru/view-cr/164_2',
    'nasopharyngeal': 'https://cr.minzdrav.gov.ru/view-cr/535_2',
    'hypopharynx': 'https://cr.minzdrav.gov.ru/view-cr/27_2',
    'laryngeal': 'https://cr.minzdrav.gov.ru/view-cr/475_3',
    'oropharynx': 'https://cr.minzdrav.gov.ru/view-cr/4_2',
    'vulvar': 'https://cr.minzdrav.gov.ru/view-cr/501_2',
    'urethral': 'https://cr.minzdrav.gov.ru/view-cr/450_3',
    'skin_bcc': 'https://cr.minzdrav.gov.ru/view-cr/467_3',
    'skin_scc': 'https://cr.minzdrav.gov.ru/view-cr/476_3',
    'uveal_melanoma': 'https://cr.minzdrav.gov.ru/view-cr/100_2',
    'merkel_cell': 'https://cr.minzdrav.gov.ru/view-cr/297_2',
    'trophoblastic': 'https://cr.minzdrav.gov.ru/view-cr/80_1',
    'retroperitoneal_sarcoma': 'https://cr.minzdrav.gov.ru/view-cr/618_3',
    'mediastinal_tumors': 'https://cr.minzdrav.gov.ru/view-cr/502_2',
    'nasal_cancer': 'https://cr.minzdrav.gov.ru/view-cr/3_2',
    'lip_cancer': 'https://cr.minzdrav.gov.ru/view-cr/553_2',
    'germ_cell_male': 'https://cr.minzdrav.gov.ru/view-cr/584_2',
    'lymphoid': 'https://cr.minzdrav.gov.ru/view-cr/139_2',
    'ovarian_borderline': 'https://cr.minzdrav.gov.ru/view-cr/346_2',
    'ovarian_nonepithelial': 'https://cr.minzdrav.gov.ru/view-cr/541_2',
    'kidney_parenchyma': 'https://cr.minzdrav.gov.ru/view-cr/10_5',
    'thyroid_medullary': 'https://cr.minzdrav.gov.ru/view-cr/332_2',
    'cns_tumors': 'https://cr.minzdrav.gov.ru/view-cr/585_2',
    'brain_metastasis': 'https://cr.minzdrav.gov.ru/view-cr/534_3',
    'cervical_cancer_neck': 'https://cr.minzdrav.gov.ru/view-cr/537_3',
}

def get_cancer_link(cancer_type: str) -> str:
    """
    Возвращает ссылку на клинические рекомендации для указанного типа рака
    """

    if cancer_type in CANCER_LINKS:
        return CANCER_LINKS[cancer_type]
    

    variations = [
        cancer_type,
        cancer_type.replace('_cancer', ''),
        cancer_type.replace('cancer', ''),
        cancer_type.replace('_', ''),
    ]
    
    for var in variations:
        if var in CANCER_LINKS:
            return CANCER_LINKS[var]
    

    return "https://cr.minzdrav.gov.ru/rubricator"