import { motion } from "motion/react";
import { 
  CheckCircle, AlertTriangle, AlertCircle, BookOpen, 
  MessageCircle, ArrowRight, Shield, ExternalLink, FileText,
  Scale, Stethoscope, Calendar, ClipboardList, Users,
  ChevronDown, ChevronRight, Activity, Clock, Info,
  PlusCircle, RefreshCw, Library, FileCheck, Award,
  Link, ChevronLeft, Sparkles, Filter, Star, X, XCircle, HelpCircle
} from "lucide-react";
import { useState, useEffect } from "react";
import { MissingInfoCollector } from "./MissingInfoCollector";

interface ResultsViewProps {
  userType: "doctor" | "patient";
}

interface KnowledgeBaseVerification {
  found: boolean;
  recommended_regimens: string[];
  protocol_count: number;
  filtered_count?: number;
  matching_protocols?: any[];
  message: string;
}

interface Finding {
  category: string;
  prescribed: string;
  treatment?: string;
  status: string;
  comment: string;
  sources?: string[];
  protocol?: string;
  line?: number | string;
  line_response?: string;
  score_contributed?: number;
  kb_verification?: KnowledgeBaseVerification;
}

interface DoctorVersion {
  summary: string;
  compliance_score: number;
  diagnosis: {
    extracted: string;
    stage: string;
    notes: string;
  };
  findings: Finding[];
  references: string[];
  missing_info?: any;
  kb_recommendations?: string[];
  kb_protocols?: any[];
  kb_important_notes?: any[];
  kb_document?: {
    title: string;
    id: string;
    year: number;
    url: string;
    source: string;
    developers: string[];
  };
  kb_filter_note?: string;
  kb_total_protocols?: number;
  kb_relevant_count?: number;
  detected_biomarkers?: Record<string, any>;
  minzdrav_link?: string;
  international_guidelines?: {
    nccn: {
      url: string;
      name: string;
      source: string;
    };
    esmo: {
      url: string;
      name: string;
      source: string;
    };
  };
  treatment_lines?: any[];
  planned_treatment?: any;
  extracted_treatments?: string[];
  compliance_details?: {
    findings?: Finding[];
    level?: string;
    source?: string;
    message?: string;
    analyzed_lines?: number;
    protocols_available?: number;
  };
}

interface AiResponse {
  doctor_version: DoctorVersion;
  patient_version: any;
  analysis_id: string;
  original_history: string;
  cancer_type: string;
}

// Функция для получения стиля в зависимости от статуса
const getStatusStyle = (status: string) => {
  switch (status) {
    case 'correct':
      return {
        bg: 'bg-green-50',
        border: 'border-green-500',
        borderLight: 'border-green-200',
        text: 'text-green-700',
        textDark: 'text-green-800',
        icon: <CheckCircle size={20} className="text-green-600" />,
        label: '✅ Соответствует',
        badge: 'bg-green-100 text-green-700 border-green-200'
      };
    case 'warning':
      return {
        bg: 'bg-amber-50',
        border: 'border-amber-500',
        borderLight: 'border-amber-200',
        text: 'text-amber-700',
        textDark: 'text-amber-800',
        icon: <AlertTriangle size={20} className="text-amber-600" />,
        label: '⚠️ Требует внимания',
        badge: 'bg-amber-100 text-amber-700 border-amber-200'
      };
    case 'info':
      return {
        bg: 'bg-blue-50',
        border: 'border-blue-500',
        borderLight: 'border-blue-200',
        text: 'text-blue-700',
        textDark: 'text-blue-800',
        icon: <Info size={20} className="text-blue-600" />,
        label: 'ℹ️ Информация',
        badge: 'bg-blue-100 text-blue-700 border-blue-200'
      };
    case 'critical':
      return {
        bg: 'bg-red-50',
        border: 'border-red-500',
        borderLight: 'border-red-200',
        text: 'text-red-700',
        textDark: 'text-red-800',
        icon: <XCircle size={20} className="text-red-600" />,
        label: '❌ Критическое несоответствие',
        badge: 'bg-red-100 text-red-700 border-red-200'
      };
    case 'error':
      return {
        bg: 'bg-red-50',
        border: 'border-red-500',
        borderLight: 'border-red-200',
        text: 'text-red-700',
        textDark: 'text-red-800',
        icon: <AlertCircle size={20} className="text-red-600" />,
        label: '❌ Ошибка',
        badge: 'bg-red-100 text-red-700 border-red-200'
      };
    default:
      return {
        bg: 'bg-slate-50',
        border: 'border-slate-400',
        borderLight: 'border-slate-200',
        text: 'text-slate-600',
        textDark: 'text-slate-700',
        icon: <HelpCircle size={20} className="text-slate-500" />,
        label: 'Не определено',
        badge: 'bg-slate-100 text-slate-600 border-slate-200'
      };
  }
};

export function ResultsView({ userType }: ResultsViewProps) {
  const isDoctor = userType === "doctor";
  const [aiResponse, setAiResponse] = useState<AiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    'staging': true,
    'treatment': false,
    'chemo': false,
    'quality': false,
    'kb_protocols': true,
    'kb_notes': false
  });
  const [patientId, setPatientId] = useState<string>("");
  const [showMissingInfo, setShowMissingInfo] = useState(false);
  const [missingInfo, setMissingInfo] = useState<any>(null);
  const [showSuccess, setShowSuccess] = useState(false);
  const [showProtocolFilters, setShowProtocolFilters] = useState(false);
  const [protocolFilter, setProtocolFilter] = useState<string>('all');
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState("");
  const [highlightedSections, setHighlightedSections] = useState<Set<string>>(new Set());
  const [updatedFields, setUpdatedFields] = useState<string[]>([]);
  const [showUpdateBanner, setShowUpdateBanner] = useState(false);
  const [activeSection, setActiveSection] = useState('overview');

  useEffect(() => {
    const saved = localStorage.getItem('aiResult');
    const savedPatientId = localStorage.getItem('patientId');
    
    if (savedPatientId) {
      setPatientId(savedPatientId);
    }
    
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        console.log("📊 Данные из localStorage:", parsed);
        setAiResponse(parsed);
        
        if (parsed.doctor_version?.missing_info) {
          setMissingInfo(parsed.doctor_version.missing_info);
        }
      } catch (e) {
        console.error("Ошибка парсинга:", e);
      }
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    if (showUpdateBanner) {
      setTimeout(() => {
        window.scrollTo({
          top: 0,
          behavior: 'smooth'
        });
      }, 100);
    }
  }, [showUpdateBanner]);

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const formatCancerType = (type: string): string => {
    const types: { [key: string]: string } = {
      'breast': 'Рак молочной железы',
      'skin': 'Склероз',
      'lung': 'Рак легкого',
      'colon': 'Рак ободочной кишки',
      'rectal': 'Рак прямой кишки',
      'prostate': 'Рак предстательной железы',
      'pancreatic': 'Рак поджелудочной железы',
      'esophageal': 'Рак пищевода',
      'stomach': 'Рак желудка',
      'liver': 'Рак печени',
      'kidney': 'Рак почки',
      'bladder': 'Рак мочевого пузыря',
      'ovarian': 'Рак яичников',
      'cervical': 'Рак шейки матки',
      'uterine': 'Рак матки',
      'melanoma': 'Меланома',
      'head_neck': 'Рак головы и шеи',
      'thyroid': 'Рак щитовидной железы',
      'brain': 'Опухоль головного мозга',
      'soft_tissue_sarcoma': 'Саркома мягких тканей',
      'bone_sarcoma': 'Саркома кости',
      'gist': 'GIST',
      'anal': 'Рак анального канала',
      'testicular': 'Рак яичка',
      'cancer_unknown_primary': 'CUP (неизвестный первичный очаг)',
      'general': 'Злокачественное новообразование'
    };
    
    return types[type] || type;
  };

  const handleMissingInfoComplete = async (answers: Record<string, string>, impactsScore: boolean) => {
    console.log("✅ MissingInfoCollector завершил работу, answers:", answers);
    
    setShowMissingInfo(false);
    await new Promise(resolve => setTimeout(resolve, 300));
    setShowSuccess(true);
    
    try {
      const response = await fetch('http://localhost:5000/api/update-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patientId: patientId,
          analysisId: aiResponse?.analysis_id,
          answers: answers,
          originalHistory: aiResponse?.original_history || '',
          cancerType: aiResponse?.cancer_type || ''
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        const oldResponse = aiResponse;
        
        localStorage.setItem('aiResult', JSON.stringify(data.result));
        setAiResponse(data.result);
        setMissingInfo(null);
        setUpdatedFields(Object.keys(answers));
        
        const changed = new Set<string>();
        
        if (oldResponse?.doctor_version?.compliance_score !== data.result.doctor_version?.compliance_score) {
          changed.add('score');
        }
        
        if (JSON.stringify(oldResponse?.doctor_version?.diagnosis) !== 
            JSON.stringify(data.result.doctor_version?.diagnosis)) {
          changed.add('diagnosis');
        }
        
        if (JSON.stringify(oldResponse?.doctor_version?.findings) !== 
            JSON.stringify(data.result.doctor_version?.findings)) {
          changed.add('findings');
        }
        
        setHighlightedSections(changed);
        setShowUpdateBanner(true);
        
        setTimeout(() => {
          setShowSuccess(false);
          
          const fieldNames = Object.keys(answers);
          setToastMessage(`✅ Анализ обновлен! ${impactsScore ? 'Оценка пересчитана' : ''}`);
          setShowToast(true);
          
          setTimeout(() => {
            setShowToast(false);
          }, 5000);
        }, 2000);
      } else {
        console.error('Ошибка при обновлении анализа:', data.error);
        alert('Ошибка при обновлении анализа: ' + data.error);
        setShowSuccess(false);
      }
    } catch (error) {
      console.error('Ошибка при обновлении анализа:', error);
      alert('Ошибка при обновлении анализа');
      setShowSuccess(false);
    }
  };

  const handleCloseMissingInfo = () => {
    console.log("❌ Закрытие MissingInfoCollector без сохранения");
    setShowMissingInfo(false);
  };

  const formatProtocolName = (protocol: any): string => {
    const name = protocol.protocol_name || '';
    
    if (name.includes('for HER2-overexpressing')) {
      return 'Таргетная терапия при HER2-позитивных опухолях';
    }
    if (name.includes('for BRAF V600E')) {
      return 'Таргетная терапия при мутации BRAF V600E';
    }
    if (name.includes('for MET exon 14 skipping')) {
      return 'Таргетная терапия при мутации MET';
    }
    if (name.includes('for RET fusion-positive')) {
      return 'Таргетная терапия при транслокации RET';
    }
    if (name.includes('for NTRK fusion-positive')) {
      return 'Таргетная терапия при слиянии NTRK';
    }
    if (name.includes('Trastuzumab deruxtecan')) {
      return 'Трастузумаб дерукстекан (при HER2+)';
    }
    
    return name.replace(/\([^)]*\)/g, '').trim() || name;
  };

  const isRelevantForHer2 = (protocol: any): boolean => {
    const name = protocol.protocol_name?.toLowerCase() || '';
    const meds = protocol.medications?.map((m: string) => m.toLowerCase()) || [];
    const condition = protocol.condition?.toLowerCase() || '';
    
    return name.includes('her2') || 
           name.includes('trastuzumab') ||
           meds.some(m => m.includes('трастузумаб')) ||
           meds.some(m => m.includes('тукатиниб')) ||
           condition.includes('her2');
  };

  const isImmunotherapy = (protocol: any): boolean => {
    const name = protocol.protocol_name?.toLowerCase() || '';
    const meds = protocol.medications?.map((m: string) => m.toLowerCase()) || [];
    
    const immunoKeywords = ['пембролизумаб', 'ниволумаб', 'атезолизумаб', 'дурвалумаб', 'ipilimumab', 'pd-1', 'pd-l1'];
    
    return immunoKeywords.some(k => name.includes(k) || meds.some(m => m.includes(k)));
  };

  const isTargetedTherapy = (protocol: any): boolean => {
    const name = protocol.protocol_name?.toLowerCase() || '';
    const meds = protocol.medications?.map((m: string) => m.toLowerCase()) || [];
    
    const targetedKeywords = ['трастузумаб', 'тукатиниб', 'лапатиниб', 'осимертиниб', 'гефитиниб', 
                               'алектиниб', 'кризотиниб', 'дабрафениб', 'траметиниб'];
    
    return targetedKeywords.some(k => name.includes(k) || meds.some(m => m.includes(k)));
  };

  const filterProtocols = (protocols: any[]): any[] => {
    if (!protocols) return [];
    
    let filtered = protocols;
    
    switch (protocolFilter) {
      case 'relevant':
        filtered = protocols.filter(p => p.relevance_score > 0);
        break;
      case 'her2':
        filtered = protocols.filter(p => isRelevantForHer2(p));
        break;
      case 'immuno':
        filtered = protocols.filter(p => isImmunotherapy(p));
        break;
      case 'targeted':
        filtered = protocols.filter(p => isTargetedTherapy(p));
        break;
      default:
        break;
    }
    
    return filtered.sort((a, b) => (b.relevance_score || 0) - (a.relevance_score || 0));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Загрузка результатов...</p>
        </div>
      </div>
    );
  }

  if (!aiResponse) {
    return (
      <div className="text-center py-12 text-red-500">
        ❌ Нет данных. Сначала выполните проверку!
      </div>
    );
  }

  // РЕЖИМ ПАЦИЕНТА
  if (!isDoctor) {
    const patient = aiResponse.patient_version || {};
    const doctor = aiResponse.doctor_version || {};
    const missingInfoData = doctor.missing_info;
    const score = doctor.compliance_score || 0;
    
    const getScoreInfo = () => {
      if (score >= 95) return { color: 'purple', text: 'Идеальное соответствие', bg: 'bg-purple-50', border: 'border-purple-200', progress: 'bg-purple-500' };
      if (score >= 85) return { color: 'green', text: 'Отличное соответствие', bg: 'bg-green-50', border: 'border-green-200', progress: 'bg-green-500' };
      if (score >= 75) return { color: 'teal', text: 'Хорошее соответствие', bg: 'bg-teal-50', border: 'border-teal-200', progress: 'bg-teal-500' };
      if (score >= 65) return { color: 'blue', text: 'Среднее соответствие', bg: 'bg-blue-50', border: 'border-blue-200', progress: 'bg-blue-500' };
      if (score >= 50) return { color: 'amber', text: 'Низкое соответствие', bg: 'bg-amber-50', border: 'border-amber-200', progress: 'bg-amber-500' };
      return { color: 'red', text: 'Критическое несоответствие', bg: 'bg-red-50', border: 'border-red-200', progress: 'bg-red-500' };
    };
    
    const scoreInfo = getScoreInfo();
    
    const scrollToSection = (sectionId: string) => {
      const element = document.getElementById(sectionId);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    };
    
    return (
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-3xl mx-auto px-4 py-8"
      >
        {/* Боковая навигация */}
        <div className="fixed left-4 top-1/2 transform -translate-y-1/2 hidden lg:block space-y-2">
          <button onClick={() => scrollToSection('compliance')} 
                  className="w-10 h-10 rounded-full bg-white shadow-md flex items-center justify-center text-slate-600 hover:bg-teal-50 hover:text-teal-600 transition-all border border-slate-200">
            📊
          </button>
          <button onClick={() => scrollToSection('analysis')} 
                  className="w-10 h-10 rounded-full bg-white shadow-md flex items-center justify-center text-slate-600 hover:bg-teal-50 hover:text-teal-600 transition-all border border-slate-200">
            📋
          </button>
          {patient.compliant_treatments?.length > 0 && (
            <button onClick={() => scrollToSection('correct')} 
                    className="w-10 h-10 rounded-full bg-white shadow-md flex items-center justify-center text-slate-600 hover:bg-green-50 hover:text-green-600 transition-all border border-slate-200">
              ✅
            </button>
          )}
          {patient.treatment_warnings?.length > 0 && (
            <button onClick={() => scrollToSection('warnings')} 
                    className="w-10 h-10 rounded-full bg-white shadow-md flex items-center justify-center text-slate-600 hover:bg-amber-50 hover:text-amber-600 transition-all border border-slate-200">
              ⚠️
            </button>
          )}
          {patient.key_points?.length > 0 && (
            <button onClick={() => scrollToSection('keypoints')} 
                    className="w-10 h-10 rounded-full bg-white shadow-md flex items-center justify-center text-slate-600 hover:bg-blue-50 hover:text-blue-600 transition-all border border-slate-200">
              📌
            </button>
          )}
          {patient.questions_for_doctor?.length > 0 && (
            <button onClick={() => scrollToSection('questions')} 
                    className="w-10 h-10 rounded-full bg-white shadow-md flex items-center justify-center text-slate-600 hover:bg-purple-50 hover:text-purple-600 transition-all border border-slate-200">
              ❓
            </button>
          )}
          {(patient.minzdrav_link || patient.international_guidelines) && (
            <button onClick={() => scrollToSection('links')} 
                    className="w-10 h-10 rounded-full bg-white shadow-md flex items-center justify-center text-slate-600 hover:bg-slate-100 hover:text-slate-700 transition-all border border-slate-200">
              🔗
            </button>
          )}
        </div>

        {/* Мобильная навигация */}
        <div className="lg:hidden sticky top-16 z-10 bg-white/90 backdrop-blur-sm border-b pb-2 mb-4 flex gap-2 overflow-x-auto">
          <a href="#compliance" className="text-sm px-3 py-1 bg-slate-100 rounded-full">📊 Соответствие</a>
          <a href="#analysis" className="text-sm px-3 py-1 bg-slate-100 rounded-full">📋 Анализ</a>
          {patient.compliant_treatments?.length > 0 && <a href="#correct" className="text-sm px-3 py-1 bg-slate-100 rounded-full">✅ Верно</a>}
          {patient.treatment_warnings?.length > 0 && <a href="#warnings" className="text-sm px-3 py-1 bg-slate-100 rounded-full">⚠️ Замечания</a>}
          {patient.key_points?.length > 0 && <a href="#keypoints" className="text-sm px-3 py-1 bg-slate-100 rounded-full">📌 Моменты</a>}
          {patient.questions_for_doctor?.length > 0 && <a href="#questions" className="text-sm px-3 py-1 bg-slate-100 rounded-full">❓ Вопросы</a>}
          {(patient.minzdrav_link || patient.international_guidelines) && <a href="#links" className="text-sm px-3 py-1 bg-slate-100 rounded-full">🔗 Ссылки</a>}
        </div>

        {/* Соответствие стандартам */}
        <section id="compliance" className="scroll-mt-24 mb-6">
          <div className={`p-6 rounded-xl border ${scoreInfo.bg} ${scoreInfo.border}`}>
            <div className="flex items-center justify-between mb-3">
              <div>
                <h2 className="text-xl font-bold text-slate-800">Соответствие стандартам</h2>
                <p className={`text-lg font-medium text-${scoreInfo.color}-700 mt-1`}>{scoreInfo.text}</p>
              </div>
              <div className={`text-5xl font-bold text-${scoreInfo.color}-600`}>{score}%</div>
            </div>
            <div className="h-3 bg-white rounded-full overflow-hidden">
              <div className={`h-full rounded-full ${scoreInfo.progress}`} style={{ width: `${score}%` }} />
            </div>
          </div>
        </section>

        {/* Анализ лечения */}
        {patient.summary && (
          <section id="analysis" className="scroll-mt-24 mb-6">
            <div className="bg-gradient-to-br from-teal-50 to-blue-50 p-6 rounded-xl border border-teal-200 shadow-sm">
              <h3 className="text-lg font-semibold text-teal-800 mb-3 flex items-center gap-2">
                <FileText size={20} />
                Анализ лечения
              </h3>
              <p className="text-slate-700 leading-relaxed">{patient.summary}</p>
            </div>
          </section>
        )}

        {/* Недостающая информация */}
        {missingInfoData && !showSuccess && (
          <div className="bg-amber-50 p-6 rounded-xl border-l-4 border-amber-500 mb-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="text-amber-600 shrink-0 mt-1" size={24} />
              <div>
                <h3 className="font-semibold text-amber-800 text-lg">Нужны уточнения</h3>
                <p className="text-amber-700 text-sm mb-3">{missingInfoData.message}</p>
                <button 
                  onClick={() => setShowMissingInfo(true)}
                  className="bg-amber-600 text-white px-4 py-2 rounded-lg hover:bg-amber-700 transition-colors text-sm"
                >
                  Добавить информацию
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Верные назначения */}
        {patient.compliant_treatments?.length > 0 && (
          <section id="correct" className="scroll-mt-24 mb-6">
            <h3 className="text-lg font-semibold text-green-700 mb-3 flex items-center gap-2">
              <CheckCircle size={20} /> ✅ Что назначено верно
            </h3>
            <div className="space-y-3">
              {patient.compliant_treatments.map((item: string, idx: number) => (
                <div key={idx} className="p-4 bg-green-50 rounded-lg border-l-4 border-green-500">
                  <p className="text-sm text-green-800">{item.replace('✓', '').trim()}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Замечания */}
        {patient.treatment_warnings?.length > 0 && (
          <section id="warnings" className="scroll-mt-24 mb-6">
            <h3 className="text-lg font-semibold text-amber-700 mb-3 flex items-center gap-2">
              <AlertTriangle size={20} /> ⚠️ На что обратить внимание
            </h3>
            <div className="space-y-3">
              {patient.treatment_warnings.map((item: string, idx: number) => (
                <div key={idx} className="p-4 bg-amber-50 rounded-lg border-l-4 border-amber-500">
                  <p className="text-sm text-amber-800">{item.replace('⚠️', '').trim()}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Ключевые моменты */}
        {patient.key_points?.length > 0 && (
          <section id="keypoints" className="scroll-mt-24 mb-6">
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Sparkles size={20} className="text-teal-600" />
                Ключевые моменты
              </h3>
              <ul className="space-y-3">
                {patient.key_points.map((point: string, idx: number) => (
                  <li key={idx} className="flex gap-3">
                    <span className="w-6 h-6 rounded-full bg-teal-100 flex items-center justify-center text-teal-600 text-sm shrink-0">
                      {idx + 1}
                    </span>
                    <span className="text-slate-700">{point}</span>
                  </li>
                ))}
              </ul>
            </div>
          </section>
        )}

        {/* Вопросы врачу */}
        {patient.questions_for_doctor?.length > 0 && (
          <section id="questions" className="scroll-mt-24 mb-6">
            <div className="bg-blue-50 p-6 rounded-xl border border-blue-200">
              <h3 className="text-lg font-semibold text-blue-800 mb-4 flex items-center gap-2">
                <MessageCircle size={20} /> Вопросы для врача
              </h3>
              <ul className="space-y-3">
                {patient.questions_for_doctor.map((q: string, idx: number) => (
                  <li key={idx} className="flex gap-3 text-blue-800">
                    <ArrowRight size={18} className="shrink-0 mt-1 text-blue-500" />
                    <span>{q}</span>
                  </li>
                ))}
              </ul>
            </div>
          </section>
        )}

        {/* Ссылки */}
        {(patient.minzdrav_link || patient.international_guidelines) && (
          <section id="links" className="scroll-mt-24 mb-6">
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <Link size={20} className="text-teal-600" />
              Полезные ссылки
            </h3>
            <div className="flex flex-wrap gap-2">
              {patient.minzdrav_link && (
                <a href={patient.minzdrav_link} target="_blank" 
                  className="px-4 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 flex items-center gap-2 border border-blue-200">
                  Минздрав РФ <ExternalLink size={14} />
                </a>
              )}
              {patient.international_guidelines?.nccn && (
                <a href={patient.international_guidelines.nccn.url} target="_blank"
                  className="px-4 py-2 bg-green-50 text-green-700 rounded-lg hover:bg-green-100 flex items-center gap-2 border border-green-200">
                  NCCN <ExternalLink size={14} />
                </a>
              )}
              {patient.international_guidelines?.esmo && (
                <a href={patient.international_guidelines.esmo.url} target="_blank"
                  className="px-4 py-2 bg-orange-50 text-orange-700 rounded-lg hover:bg-orange-100 flex items-center gap-2 border border-orange-200">
                  ESMO <ExternalLink size={14} />
                </a>
              )}
            </div>
          </section>
        )}

        {/* Анонимность */}
        <div className="text-center text-xs text-slate-400 pt-4 border-t flex items-center justify-center gap-1">
          <Shield size={14} />
          Данные обработаны анонимно
        </div>

        {/* Окно обновления */}
        {showSuccess && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 text-center"
            >
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle size={40} className="text-green-600" />
              </div>
              <h3 className="text-2xl font-bold text-slate-800 mb-2">Информация получена!</h3>
              <p className="text-slate-600 mb-6">
                Спасибо! Мы обновляем анализ с учетом новой информации.
              </p>
              <div className="bg-green-50 rounded-lg p-4 mb-6">
                <p className="text-sm text-green-700">
                  Обновленный анализ появится через несколько секунд.
                </p>
              </div>
              <div className="flex justify-center">
                <RefreshCw size={24} className="animate-spin text-teal-600" />
              </div>
            </motion.div>
          </motion.div>
        )}

        {/* Модалка сбора информации */}
        {showMissingInfo && missingInfoData && (
          <MissingInfoCollector
            patientId={patientId}
            missingInfo={missingInfoData.fields || missingInfoData}
            originalHistory={aiResponse?.original_history || ''}
            cancerType={aiResponse?.cancer_type || ''}
            userType={userType}
            onComplete={handleMissingInfoComplete}
            onClose={handleCloseMissingInfo}
          />
        )}

        {/* Всплывающее уведомление */}
        {showToast && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className="fixed bottom-6 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-green-500 to-teal-500 text-white px-6 py-4 rounded-xl shadow-2xl z-50 flex items-center gap-4 max-w-md"
          >
            <CheckCircle size={24} className="shrink-0" />
            <div className="flex-1">
              <p className="font-bold text-lg">Информация обновлена!</p>
              <p className="text-sm text-green-100 mt-1">{toastMessage}</p>
            </div>
            <button 
              onClick={() => setShowToast(false)}
              className="p-1.5 hover:bg-green-600 rounded-lg transition-colors"
            >
              <X size={20} />
            </button>
          </motion.div>
        )}
      </motion.div>
    );
  }

  // ========== РЕЖИМ ВРАЧА ==========
  const doctor = aiResponse.doctor_version || {};
  const findings = doctor.findings || [];
  const complianceDetails = doctor.compliance_details || {};
  const detailsFindings = complianceDetails.findings || [];
  const missingInfoData = doctor.missing_info;
  const cancerType = aiResponse.cancer_type || 'general';
  
  const kbProtocols = doctor.kb_protocols || [];
  const kbImportantNotes = doctor.kb_important_notes || [];
  const kbDocument = doctor.kb_document;
  const biomarkers = doctor.detected_biomarkers || {};
  
  // Объединяем findings из разных источников
  const allFindings = [...findings, ...detailsFindings].filter(
    (f, index, self) => 
      index === self.findIndex((t) => 
        t.treatment === f.treatment && t.comment === f.comment
      )
  );
  
  const filteredProtocols = filterProtocols(kbProtocols);

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-6xl mx-auto px-4 py-8 space-y-6"
    >
      {/* Боковая навигация для врача */}
      <div className="fixed left-4 top-1/2 transform -translate-y-1/2 hidden lg:block space-y-2 z-10">
        <button 
          onClick={() => scrollToSection('doctor-summary')} 
          className="w-10 h-10 rounded-full bg-white shadow-md flex items-center justify-center text-slate-600 hover:bg-teal-50 hover:text-teal-600 transition-all border border-slate-200"
          title="Общий анализ"
        >
          📊
        </button>
        <button 
          onClick={() => scrollToSection('doctor-diagnosis')} 
          className="w-10 h-10 rounded-full bg-white shadow-md flex items-center justify-center text-slate-600 hover:bg-teal-50 hover:text-teal-600 transition-all border border-slate-200"
          title="Диагноз"
        >
          📋
        </button>
        <button 
          onClick={() => scrollToSection('doctor-findings')} 
          className="w-10 h-10 rounded-full bg-white shadow-md flex items-center justify-center text-slate-600 hover:bg-teal-50 hover:text-teal-600 transition-all border border-slate-200"
          title="Назначения"
        >
          🔍
        </button>
        <button 
          onClick={() => scrollToSection('doctor-sources')} 
          className="w-10 h-10 rounded-full bg-white shadow-md flex items-center justify-center text-slate-600 hover:bg-teal-50 hover:text-teal-600 transition-all border border-slate-200"
          title="Источники"
        >
          📖
        </button>
      </div>

      {/* Баннер с типом рака */}
      <div id="doctor-summary" className="bg-gradient-to-r from-cyan-600 to-teal-500 rounded-xl p-4 text-white shadow-lg scroll-mt-24">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Library size={24} />
            <div>
              <h2 className="text-xl font-bold">{formatCancerType(cancerType)}</h2>
              <p className="text-teal-100 text-sm">Анализ с использованием стандартов Минздрава РФ, NCCN, ESMO</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold">{doctor.compliance_score || 0}%</div>
            <div className="text-xs text-teal-100">соответствие</div>
          </div>
        </div>
      </div>

      

      {/* Диагноз */}
      {doctor.diagnosis && (
        <div id="doctor-diagnosis" className={`bg-white rounded-xl p-6 shadow-lg border-2 transition-all duration-500 scroll-mt-24 ${
          highlightedSections.has('diagnosis') 
            ? 'border-green-500 shadow-green-200' 
            : 'border-slate-200'
        }`}>
          <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
            <FileText size={18} className="text-teal-600" />
            Диагноз
          </h3>
          <div className="bg-slate-50 p-4 rounded-xl">
            <p className="font-mono text-slate-800">{doctor.diagnosis.extracted || "Не указан"}</p>
            <div className="flex items-center gap-3 mt-2 text-sm">
              <span className="text-slate-500">Стадия:</span>
              <span className="font-medium text-teal-700">{doctor.diagnosis.stage || "Не указана"}</span>
            </div>
            {doctor.diagnosis.notes && (
              <p className="text-sm text-slate-500 mt-2">{doctor.diagnosis.notes}</p>
            )}
          </div>
        </div>
      )}

      {/* Молекулярно-генетические характеристики */}
      {Object.keys(biomarkers).length > 0 && (
        <div id="doctor-biomarkers" className="bg-white rounded-xl p-6 shadow-lg border border-slate-200 scroll-mt-24">
          <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
            <Sparkles size={18} className="text-teal-600" />
            Молекулярно-генетические характеристики
          </h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(biomarkers).map(([key, value]) => {
              if (!value) return null;
              
              const biomarkerNames: Record<string, string> = {
                'her2_positive': 'HER2+ (3+)',
                'her2_negative': 'HER2-',
                'egfr_mutated': 'EGFR мутация',
                'alk_positive': 'ALK+',
                'ros1_positive': 'ROS1+',
                'braf_mutated': 'BRAF мутация',
                'pd_l1_high': 'PD-L1 высокий',
                'mss': 'MSS',
                'tp53_mutated': 'TP53 мутация',
                'cup': 'CUP (неизвестный первичный очаг)',
                'triple_negative': 'Трижды негативный'
              };
              
              const colors: Record<string, string> = {
                'her2_positive': 'bg-purple-100 text-purple-800 border-purple-200',
                'her2_negative': 'bg-gray-100 text-gray-800 border-gray-200',
                'egfr_mutated': 'bg-blue-100 text-blue-800 border-blue-200',
                'alk_positive': 'bg-blue-100 text-blue-800 border-blue-200',
                'ros1_positive': 'bg-blue-100 text-blue-800 border-blue-200',
                'braf_mutated': 'bg-amber-100 text-amber-800 border-amber-200',
                'pd_l1_high': 'bg-green-100 text-green-800 border-green-200',
                'mss': 'bg-gray-100 text-gray-800 border-gray-200',
                'tp53_mutated': 'bg-red-100 text-red-800 border-red-200',
                'cup': 'bg-amber-100 text-amber-800 border-amber-200',
                'triple_negative': 'bg-red-100 text-red-800 border-red-200'
              };
              
              return (
                <span key={key} className={`px-3 py-1 rounded-full text-sm border ${colors[key] || 'bg-slate-100 text-slate-800'}`}>
                  {biomarkerNames[key] || key}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {/* Общее предупреждение о недостающей информации */}
      {missingInfoData && !showSuccess && (
        <div className="bg-amber-50 rounded-xl p-6 border-l-8 border-amber-500">
          <div className="flex items-start gap-4">
            <AlertCircle size={24} className="text-amber-600 shrink-0 mt-1" />
            <div className="flex-1">
              <h3 className="font-bold text-lg text-amber-800 mb-2">
                Требуется дополнительная информация
              </h3>
              <p className="text-amber-700 mb-4">
                {missingInfoData.message || "Для более точного анализа необходимо уточнить следующие параметры:"}
              </p>
              
              <ul className="space-y-2 mb-4">
                {missingInfoData.fields?.map((field: any, idx: number) => (
                  <li key={idx} className="flex items-start gap-2 text-sm">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                    <span className="text-amber-800 font-medium">{field.question}</span>
                    <span className="text-amber-600">— {field.description}</span>
                  </li>
                ))}
              </ul>
              
              <button
                onClick={() => setShowMissingInfo(true)}
                disabled={showSuccess}
                className="inline-flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors disabled:bg-amber-300 disabled:cursor-not-allowed"
              >
                <PlusCircle size={18} />
                Добавить информацию
              </button>
            </div>
          </div>
        </div>
      )}

    
      {/* Детальный разбор назначений */}
      {allFindings.length > 0 && (
        <div id="doctor-findings" className="space-y-4 scroll-mt-24">
          <h3 className="font-bold text-xl flex items-center gap-2">
            <AlertCircle size={20} className="text-teal-600" />
            Детальный разбор назначений
          </h3>

          {allFindings
            .filter(item => {
              const category = (item.category || '').toLowerCase();
              // Оставляем только нужные категории
              return category.includes('хирург') || 
                    category.includes('лучев') || 
                    category.includes('таргет') || 
                    category.includes('химио');
            })
            .map((item: any, idx: number) => {
              const style = getStatusStyle(item.status);
              
              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  className={`${style.bg} rounded-xl p-6 shadow-lg border-l-8 ${style.border} border-2 transition-all duration-500 ${
                    highlightedSections.has('findings') && idx === 0
                      ? 'border-green-500 shadow-green-200' 
                      : ''
                  }`}
                >
                  <div className="flex justify-between items-start mb-4">
                    <h4 className="font-bold text-lg flex items-center gap-2">
                      {style.icon}
                      {item.category || 'Назначение'} 
                      {item.line && (
                        <span className="text-sm font-normal bg-white px-2 py-0.5 rounded-full">
                          линия {item.line}
                        </span>
                      )}
                    </h4>
                    <div className={`px-3 py-1 rounded-full text-sm font-medium ${style.badge}`}>
                      {style.label}
                    </div>
                  </div>
                  
                  <div className="grid md:grid-cols-2 gap-4 mb-4">
                    <div className="bg-white p-3 rounded-lg">
                      <p className="text-xs text-slate-500 mb-1">Назначено:</p>
                      <p className="font-medium">{item.prescribed || item.treatment || "Не указано"}</p>
                    </div>
                    <div className="bg-white p-3 rounded-lg">
                      <p className="text-xs text-slate-500 mb-1">Комментарий:</p>
                      <p className="font-medium">{item.comment}</p>
                    </div>
                  </div>

                  {/* Информация о протоколе */}
                  {item.protocol && (
                    <div className="mt-2 p-3 bg-white rounded-lg border border-slate-200">
                      <p className="text-xs text-slate-500">Протокол:</p>
                      <p className="text-sm font-medium">{item.protocol}</p>
                    </div>
                  )}

                  {/* Информация из базы знаний */}
                  {item.kb_verification && (
                    <div className="mt-4 p-4 bg-teal-50 rounded-lg border border-teal-200">
                      <div className="flex items-start gap-2">
                        <Award size={18} className="text-teal-600 shrink-0 mt-0.5" />
                        <div className="flex-1">
                          <p className="text-sm font-medium text-teal-800 mb-2">
                            {item.kb_verification.message}
                          </p>
                          {item.kb_verification.recommended_regimens?.length > 0 && (
                            <>
                              <p className="text-xs text-teal-600 mb-1">Рекомендованные режимы:</p>
                              <div className="flex flex-wrap gap-1">
                                {item.kb_verification.recommended_regimens.slice(0, 5).map((reg: string, i: number) => (
                                  <span key={i} className="text-xs bg-white text-teal-800 px-2 py-1 rounded border border-teal-200">
                                    {reg}
                                  </span>
                                ))}
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </motion.div>
              );
            })}
        </div>
      )}

      {/* Использованные источники */}
      {(doctor.minzdrav_link || doctor.international_guidelines?.nccn || doctor.international_guidelines?.esmo) ? (
        <div id="doctor-sources" className="bg-slate-50 rounded-xl p-6 border border-slate-200 scroll-mt-24">
          <div className="flex items-center gap-2 mb-4">
            <BookOpen size={18} className="text-teal-600" />
            <h3 className="font-bold">Использованные источники</h3>
          </div>
          
          <div className="grid md:grid-cols-3 gap-4">
            {/* Минздрав РФ */}
            {doctor.minzdrav_link && (
              <div className="bg-white p-4 rounded-lg border-l-4 border-blue-500">
                <h4 className="font-bold text-blue-800 mb-2 flex items-center gap-2">
                  <Scale size={16} />
                  Минздрав РФ
                </h4>
                <p className="text-sm text-slate-600 mb-2">
                  Клинические рекомендации
                </p>
                <a 
                  href={doctor.minzdrav_link} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-sm bg-blue-50 hover:bg-blue-100 text-blue-700 px-3 py-1.5 rounded-lg transition-colors"
                >
                  <ExternalLink size={14} />
                  <span>Открыть</span>
                </a>
              </div>
            )}
            
            {/* NCCN */}
            {doctor.international_guidelines?.nccn && (
              <div className="bg-white p-4 rounded-lg border-l-4 border-green-700">
                <h4 className="font-bold text-green-800 mb-2 flex items-center gap-2">
                  <BookOpen size={16} />
                  NCCN
                </h4>
                <p className="text-sm text-slate-600 mb-2">Clinical Practice Guidelines</p>
                <a 
                  href={doctor.international_guidelines.nccn.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-sm bg-green-50 hover:bg-green-100 text-green-700 px-3 py-1.5 rounded-lg transition-colors"
                >
                  <ExternalLink size={14} />
                  <span>Открыть</span>
                </a>
              </div>
            )}
            
            {/* ESMO */}
            {doctor.international_guidelines?.esmo && (
              <div className="bg-white p-4 rounded-lg border-l-4 border-orange-600">
                <h4 className="font-bold text-orange-800 mb-2 flex items-center gap-2">
                  <BookOpen size={16} />
                  ESMO
                </h4>
                <p className="text-sm text-slate-600 mb-2">Clinical Practice Guidelines</p>
                <a 
                  href={doctor.international_guidelines.esmo.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-sm bg-orange-50 hover:bg-orange-100 text-orange-700 px-3 py-1.5 rounded-lg transition-colors"
                >
                  <ExternalLink size={14} />
                  <span>Открыть</span>
                </a>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="bg-slate-50 rounded-xl p-6 border border-slate-200">
          <div className="flex items-center gap-2 mb-4">
            <BookOpen size={18} className="text-teal-600" />
            <h3 className="font-bold">Источники</h3>
          </div>
          <p className="text-sm text-slate-500 mb-3">
            Ссылки на конкретные рекомендации временно недоступны.
          </p>
          <a 
            href="https://cr.minzdrav.gov.ru/clin-rec"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-sm bg-teal-50 hover:bg-teal-100 text-teal-700 px-4 py-2 rounded-lg transition-colors"
          >
            <ExternalLink size={16} />
            <span>Рубрикатор клинических рекомендаций Минздрава РФ</span>
          </a>
        </div>
      )}

      {/* Анонимность */}
      <div className="flex items-center gap-2 text-xs text-slate-400">
        <Shield size={14} />
        <span>Данные обработаны анонимно в соответствии с требованиями</span>
      </div>

      {/* Модальное окно сбора информации */}
      {showMissingInfo && missingInfo && (
        <MissingInfoCollector
          patientId={patientId}
          missingInfo={missingInfo.fields || missingInfo}
          originalHistory={aiResponse?.original_history || ''}
          cancerType={aiResponse?.cancer_type || ''}
          userType={userType}
          onComplete={handleMissingInfoComplete}
          onClose={handleCloseMissingInfo}
        />
      )}

      {/* Зеленое окно успеха */}
      {showSuccess && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 text-center"
          >
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle size={40} className="text-green-600" />
            </div>
            <h3 className="text-2xl font-bold text-slate-800 mb-2">Информация получена!</h3>
            <p className="text-slate-600 mb-6">
              Спасибо! Мы обновляем анализ с учетом новой информации.
            </p>
            <div className="bg-green-50 rounded-lg p-4 mb-6">
              <p className="text-sm text-green-700">
                Обновленный анализ появится через несколько секунд.
              </p>
            </div>
            <div className="flex justify-center">
              <RefreshCw size={24} className="animate-spin text-teal-600" />
            </div>
          </motion.div>
        </motion.div>
      )}

      {/* Тост-уведомление */}
      {showToast && (
        <motion.div
          initial={{ opacity: 0, y: 50, x: '-50%' }}
          animate={{ opacity: 1, y: 0, x: '-50%' }}
          exit={{ opacity: 0, y: 50, x: '-50%' }}
          className="fixed bottom-6 left-1/2 transform -translate-x-1/2 bg-green-600 text-white px-6 py-4 rounded-xl shadow-2xl z-50 flex items-center gap-3 max-w-md"
        >
          <CheckCircle size={24} className="shrink-0" />
          <p className="font-bold">{toastMessage || "Анализ обновлен!"}</p>
        </motion.div>
      )}
    </motion.div>
  );
}