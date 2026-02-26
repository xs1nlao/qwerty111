
import json
import os
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any

class MetricsCollector:
    def __init__(self):
        self.metrics_file = "metrics_data.json"
        self.start_time = datetime.now()
        self.daily_stats = {}
        self.load_metrics()
    
    def load_metrics(self):
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.daily_stats = data.get('daily', {})
                    self.start_time = datetime.fromisoformat(data.get('start_time', datetime.now().isoformat()))
            except:
                self.daily_stats = {}
    
    def save_metrics(self):
        try:
            data = {
                'start_time': self.start_time.isoformat(),
                'daily': self.daily_stats
            }
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def get_today_key(self):
        return datetime.now().strftime('%Y-%m-%d')
    
    def record_protocol_usage(self, cancer_type: str, protocol_found: bool, source: str):
        """
        Записывает статистику использования базы протоколов
        """
        if 'protocol_stats' not in self.daily_stats:
            self.daily_stats['protocol_stats'] = {
                'minzdrav_hits': 0,
                'ai_fallbacks': 0,
                'by_cancer_type': {}
            }
        
        if protocol_found:
            self.daily_stats['protocol_stats']['minzdrav_hits'] += 1
        else:
            self.daily_stats['protocol_stats']['ai_fallbacks'] += 1
        
        if cancer_type not in self.daily_stats['protocol_stats']['by_cancer_type']:
            self.daily_stats['protocol_stats']['by_cancer_type'][cancer_type] = {
                'hits': 0, 'misses': 0
            }
        
        if protocol_found:
            self.daily_stats['protocol_stats']['by_cancer_type'][cancer_type]['hits'] += 1
        else:
            self.daily_stats['protocol_stats']['by_cancer_type'][cancer_type]['misses'] += 1
    
    def _ensure_today(self):
        today = self.get_today_key()
        if today not in self.daily_stats:
            self.daily_stats[today] = {
                'analyses': 0,
                'cache_hits': 0,
                'errors': 0,
                'response_times': [],
                'cancer_types': {},
                'compliance_scores': [],
                'mammogram': {
                    'total': 0,
                    'malignant': 0,
                    'benign': 0,
                    'confidences': []
                }
            }
        return today
    
    def record_analysis(self, cancer_type: str, compliance_score: int, response_time: float, from_cache: bool = False,
                   source: str = 'unknown'):
        try:
            today = self._ensure_today()
            
            self.daily_stats[today]['analyses'] += 1
            
            if cancer_type not in self.daily_stats[today]['cancer_types']:
                self.daily_stats[today]['cancer_types'][cancer_type] = 0
            self.daily_stats[today]['cancer_types'][cancer_type] += 1
            
            self.daily_stats[today]['compliance_scores'].append(compliance_score)
            if len(self.daily_stats[today]['compliance_scores']) > 1000:
                self.daily_stats[today]['compliance_scores'] = self.daily_stats[today]['compliance_scores'][-1000:]
            
            self.daily_stats[today]['response_times'].append(response_time)
            if len(self.daily_stats[today]['response_times']) > 1000:
                self.daily_stats[today]['response_times'] = self.daily_stats[today]['response_times'][-1000:]
            
            if from_cache:
                self.daily_stats[today]['cache_hits'] += 1
            
            self.save_metrics()
        except Exception as e:
            print(f"Metrics error: {e}")
    
    def record_mammogram_analysis(self, success: bool, is_malignant: bool, confidence: float, response_time: float):
        try:
            today = self._ensure_today()
            
            if 'mammogram' not in self.daily_stats[today]:
                self.daily_stats[today]['mammogram'] = {
                    'total': 0,
                    'malignant': 0,
                    'benign': 0,
                    'confidences': []
                }
            
            self.daily_stats[today]['mammogram']['total'] += 1
            if is_malignant:
                self.daily_stats[today]['mammogram']['malignant'] += 1
            else:
                self.daily_stats[today]['mammogram']['benign'] += 1
            
            self.daily_stats[today]['mammogram']['confidences'].append(confidence)
            if len(self.daily_stats[today]['mammogram']['confidences']) > 1000:
                self.daily_stats[today]['mammogram']['confidences'] = self.daily_stats[today]['mammogram']['confidences'][-1000:]
            
            self.save_metrics()
        except:
            pass
    
    def record_error(self, error_type: str):
        try:
            today = self._ensure_today()
            self.daily_stats[today]['errors'] += 1
            self.save_metrics()
        except:
            pass
    
    def get_metrics_report(self) -> Dict[str, Any]:
        try:
            total_analyses = 0
            total_scores = []
            total_times = []
            cancer_type_counts = {}
            total_cache_hits = 0
            total_errors = 0
            total_mammogram = 0
            total_malignant = 0
            total_benign = 0
            mammogram_confidences = []
            
            for day, stats in self.daily_stats.items():
                total_analyses += stats.get('analyses', 0)
                total_cache_hits += stats.get('cache_hits', 0)
                total_errors += stats.get('errors', 0)
                
                for ct, count in stats.get('cancer_types', {}).items():
                    cancer_type_counts[ct] = cancer_type_counts.get(ct, 0) + count
                
                scores = stats.get('compliance_scores', [])
                if isinstance(scores, list):
                    total_scores.extend(scores)
                
                times = stats.get('response_times', [])
                if isinstance(times, list):
                    total_times.extend(times)
                
                mammo = stats.get('mammogram', {})
                if mammo:
                    total_mammogram += mammo.get('total', 0)
                    total_malignant += mammo.get('malignant', 0)
                    total_benign += mammo.get('benign', 0)
                    mammogram_confidences.extend(mammo.get('confidences', []))
            
            days_passed = max(1, (datetime.now() - self.start_time).days)
            
            avg_score = sum(total_scores) / len(total_scores) if total_scores else 0
            avg_time = sum(total_times) / len(total_times) if total_times else 0
            min_time = min(total_times) if total_times else 0
            max_time = max(total_times) if total_times else 0
            
            time_dist = {
                '<1s': len([t for t in total_times if t < 1]),
                '1-2s': len([t for t in total_times if 1 <= t < 2]),
                '2-3s': len([t for t in total_times if 2 <= t < 3]),
                '3-4s': len([t for t in total_times if 3 <= t < 4]),
                '>4s': len([t for t in total_times if t >= 4])
            }
            
            score_dist = {
                'high': len([s for s in total_scores if s >= 85]),
                'medium': len([s for s in total_scores if 65 <= s < 85]),
                'low': len([s for s in total_scores if s < 65])
            }
            
            return {
                'period': {
                    'start': self.start_time.strftime('%Y-%m-%d'),
                    'end': datetime.now().strftime('%Y-%m-%d'),
                    'days': days_passed
                },
                'volume': {
                    'total_analyses': total_analyses,
                    'analyses_per_day': round(total_analyses / days_passed, 1)
                },
                'performance': {
                    'avg_response_time': round(avg_time, 2),
                    'min_response_time': round(min_time, 2),
                    'max_response_time': round(max_time, 2),
                    'response_time_distribution': time_dist
                },
                'cache': {
                    'hits': total_cache_hits,
                    'hit_rate': round(total_cache_hits / total_analyses * 100, 1) if total_analyses > 0 else 0
                },
                'quality': {
                    'avg_compliance_score': round(avg_score, 1),
                    'score_distribution': score_dist
                },
                'cancer_types': cancer_type_counts,
                'errors': {
                    'total': total_errors,
                    'error_rate': round(total_errors / total_analyses * 100, 2) if total_analyses > 0 else 0
                },
                'mammogram': {
                    'total': total_mammogram,
                    'malignant': total_malignant,
                    'benign': total_benign,
                    'malignant_rate': round(total_malignant / total_mammogram * 100, 1) if total_mammogram > 0 else 0,
                    'avg_confidence': round(sum(mammogram_confidences) / len(mammogram_confidences), 3) if mammogram_confidences else 0
                }
            }
        except Exception as e:
            print(f"Error generating metrics: {e}")
            return {}


metrics_collector = MetricsCollector()