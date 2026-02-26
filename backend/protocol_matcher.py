

class ProtocolMatcher:
    """
    Сравнивает назначенное лечение с протоколами из базы
    """
    
    def __init__(self, protocols_db: dict):
        self.protocols_db = protocols_db
    
    def find_best_match(self, cancer_type: str, line_treatments: List[str], 
                        biomarkers: dict, line_num: int) -> dict:
        """
        Находит наилучшее соответствие протоколу
        """
        protocols = self.protocols_db.get(cancer_type, [])
        
        best_match = {
            'protocol': None,
            'score': 0,
            'matches': [],
            'missing': [],
            'extra': []
        }
        
        for protocol in protocols:
            match_result = self._match_protocol(protocol, line_treatments, biomarkers, line_num)
            if match_result['score'] > best_match['score']:
                best_match = match_result
                best_match['protocol'] = protocol
        
        return best_match
    
    def _match_protocol(self, protocol: dict, treatments: List[str], 
                        biomarkers: dict, line_num: int) -> dict:
        """
        Оценивает соответствие конкретному протоколу
        """
        protocol_meds = protocol.get('medications', [])
        protocol_line = protocol.get('line', 'unknown')
        protocol_biomarkers = protocol.get('biomarkers', [])
        
        score = 0
        matches = []
        missing = []
        

        for t in treatments:
            if any(med in t for med in protocol_meds):
                score += 25
                matches.append(t)
            else:
                score += 5  
                missing.append(t)
        

        if (line_num == 1 and protocol_line == 'first_line') or \
           (line_num == 2 and protocol_line == 'second_line'):
            score += 10
        

        for biomarker, present in biomarkers.items():
            if present and biomarker in protocol_biomarkers:
                score += 15
        
        return {
            'score': score,
            'matches': matches,
            'missing': missing,
            'extra': [t for t in treatments if t not in protocol_meds]
        }