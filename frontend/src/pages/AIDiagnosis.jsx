import { useState, useEffect } from 'react';
import { usePatient } from '../context/PatientContext';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import {
  User, Stethoscope, Brain, FileText, ArrowRight, ArrowLeft,
  Upload, Search, CheckCircle, AlertTriangle, X, Loader2,
  Activity, Shield, Microscope, ClipboardList,
  Download, Phone, RefreshCw,
} from 'lucide-react';

const C = {
  primary: '#0A6E8A', primaryDark: '#064E63', primaryLight: '#E8F4F8',
  accent: '#2ECC71', accentDark: '#27AE60',
  teal: '#0E7C7B', tealLight: '#E6F7F6',
  text: '#1A202C', textSec: '#4A5568', textMuted: '#A0AEC0',
  bg: '#F0F5F7', border: '#E2E8F0',
  critical: '#E53E3E', criticalBg: '#FFF5F5',
  amber: '#D69E2E', amberBg: '#FFFFF0',
  success: '#38A169', successBg: '#F0FFF4',
};

const STEPS = [
  { id: 1, label: 'Patient Details', icon: User },
  { id: 2, label: 'Symptoms & Labs', icon: Stethoscope },
  { id: 3, label: 'Adaptive Questions', icon: Brain },
  { id: 4, label: 'Results', icon: FileText },
];

const inputStyle = {
  width: '100%', padding: '12px 16px', borderRadius: 12,
  border: `1px solid ${C.border}`, background: C.bg, fontSize: 14,
  outline: 'none', transition: 'all 0.2s', fontFamily: 'inherit',
};

const btnPrimary = {
  display: 'inline-flex', alignItems: 'center', gap: 8,
  background: `linear-gradient(135deg, ${C.primary}, ${C.teal})`,
  color: 'white', padding: '12px 28px', borderRadius: 12,
  fontWeight: 700, fontSize: 14, border: 'none', cursor: 'pointer',
  boxShadow: '0 4px 14px rgba(10,110,138,0.25)', transition: 'all 0.2s',
};

const btnSecondary = {
  display: 'inline-flex', alignItems: 'center', gap: 8,
  padding: '12px 24px', borderRadius: 12,
  border: `1px solid ${C.border}`, background: 'white',
  color: C.textSec, fontSize: 14, fontWeight: 600, cursor: 'pointer',
};

function StepIndicator({ current }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginBottom: 32 }}>
      {STEPS.map((s, i) => (
        <div key={s.id} style={{ display: 'flex', alignItems: 'center' }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8,
            padding: '8px 18px', borderRadius: 999, fontSize: 13, fontWeight: 700,
            background: s.id < current ? C.success : s.id === current ? C.primary : '#F1F5F9',
            color: s.id <= current ? 'white' : C.textMuted,
            boxShadow: s.id === current ? '0 4px 14px rgba(10,110,138,0.3)' : 'none',
            transition: 'all 0.3s',
          }}>
            {s.id < current ? <CheckCircle size={16} /> : <s.icon size={16} />}
            <span className="hidden sm:inline">{s.label}</span>
          </div>
          {i < STEPS.length - 1 && (
            <div style={{ width: 32, height: 2, margin: '0 4px', background: s.id < current ? C.success : '#E2E8F0' }} />
          )}
        </div>
      ))}
    </div>
  );
}

function SymptomTag({ symptom, selected, onClick }) {
  return (
    <button onClick={onClick} style={{
      padding: '6px 12px', borderRadius: 8, fontSize: 12, fontWeight: 600, cursor: 'pointer',
      border: `1px solid ${selected ? C.primary : C.border}`,
      background: selected ? C.primary : 'white',
      color: selected ? 'white' : C.textSec,
      transition: 'all 0.2s',
    }}>
      {symptom.replace(/_/g, ' ')}
    </button>
  );
}

function PredictionList({ predictions = [], kind = 'ml' }) {
  if (!predictions.length) return <p style={{ fontSize: 13, color: C.textMuted }}>No ranked prediction was returned.</p>;
  return predictions.slice(0, 5).map((item, index) => {
    const name = item.disease || item.condition;
    const score = kind === 'llm' ? item.llm_estimated_likelihood_percent : item.model_confidence * 100;
    return <div key={`${name}-${index}`} style={{ display: 'flex', justifyContent: 'space-between', gap: 10, padding: '5px 0', fontSize: 13, color: C.textSec }}>
      <span>{index + 1}. {name}</span><b>{Number(score || 0).toFixed(2)}%</b>
    </div>;
  });
}

export default function AIDiagnosis() {
  const {
    patientInfo, setPatientInfo, selectedSymptoms, setSelectedSymptoms,
    symptomDescription, setSymptomDescription, labReportText, setLabReportText,
    questionnaire, setQuestionnaire, questionnaireAnswers, setQuestionnaireAnswers,
    results, setResults, reset,
  } = usePatient();

  const [step, setStep] = useState(1);
  const [allSymptoms, setAllSymptoms] = useState([]);
  const [symptomSearch, setSymptomSearch] = useState('');
  const [uploading, setUploading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const [currentQ, setCurrentQ] = useState(0);

  useEffect(() => {
    axios.get('/api/symptoms').then(r => setAllSymptoms(r.data.symptoms)).catch(() => {});
  }, []);

  const filteredSymptoms = allSymptoms.filter(s => s.toLowerCase().includes(symptomSearch.toLowerCase()));

  const selectQuestionAnswer = (question, answer) => {
    setQuestionnaireAnswers({ ...questionnaireAnswers, [question.question_id]: answer });
  };

  const handleLabUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const fd = new FormData(); fd.append('file', file);
      const { data } = await axios.post('/api/parse-lab-report', fd);
      setLabReportText(data.summary);
    } catch { setError('Failed to parse lab report.'); }
    setUploading(false);
  };

  const handleGenerateQuestionnaire = async () => {
    if (selectedSymptoms.length === 0 && !symptomDescription.trim()) {
      setError('Please select symptoms or describe your condition.'); return;
    }
    setGenerating(true); setError('');
    try {
      const { data } = await axios.post('/api/generate-questionnaire', {
        patient_name: patientInfo.name, age: parseInt(patientInfo.age),
        gender: patientInfo.gender, medical_history: patientInfo.medical_history,
        selected_symptoms: selectedSymptoms, symptom_description: symptomDescription,
      });
      setQuestionnaire(data.questions); setCurrentQ(0); setStep(3);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate questionnaire.');
    }
    setGenerating(false);
  };

  const handleAnalyze = async () => {
    setAnalyzing(true); setError('');
    try {
      const { data } = await axios.post('/api/analyze', {
        patient_name: patientInfo.name, age: parseInt(patientInfo.age),
        gender: patientInfo.gender, medical_history: patientInfo.medical_history,
        selected_symptoms: selectedSymptoms, symptom_description: symptomDescription,
        questionnaire_answers: questionnaireAnswers,
        questionnaire,
        lab_report_text: labReportText || null,
      });
      setResults(data); setStep(4);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed.');
    }
    setAnalyzing(false);
  };

  const handleDownloadPDF = async () => {
    try {
      const response = await axios.post('/api/generate-pdf', {
        patient_name: patientInfo.name, age: parseInt(patientInfo.age),
        gender: patientInfo.gender, medical_history: patientInfo.medical_history, results,
      }, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement('a');
      a.href = url; a.download = `MediMitra_${patientInfo.name}_Report.pdf`; a.click();
    } catch { setError('Failed to generate PDF.'); }
  };

  const startOver = () => { reset(); setStep(1); setError(''); setCurrentQ(0); };

  const pageV = { enter: { opacity: 0, x: 50 }, center: { opacity: 1, x: 0 }, exit: { opacity: 0, x: -50 } };

  return (
    <div style={{ paddingTop: 72, minHeight: '100vh', background: C.bg }}>
      {/* Header */}
      <section style={{ background: `linear-gradient(135deg, ${C.primaryDark}, ${C.primary}, ${C.teal})`, padding: '48px 0' }}>
        <div style={{ maxWidth: 900, margin: '0 auto', padding: '0 24px', textAlign: 'center' }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)',
            borderRadius: 999, padding: '6px 16px', fontSize: 13, color: 'rgba(255,255,255,0.9)', fontWeight: 600, marginBottom: 16,
          }}>
            <Brain size={16} /> Dataset-Constrained ML Screening
          </div>
          <h1 style={{ fontSize: 34, fontWeight: 800, color: 'white' }}>Patient Screening & Care Console</h1>
          <p style={{ color: 'rgba(255,255,255,0.6)', marginTop: 8, fontSize: 14 }}>Two-pass symptom classification with dataset-driven adaptive questions</p>
        </div>
      </section>

      <div style={{ maxWidth: 900, margin: '0 auto', padding: '32px 24px' }}>
        <StepIndicator current={step} />

        {error && (
          <div style={{ background: C.criticalBg, border: `1px solid rgba(229,62,62,0.2)`, borderRadius: 12, padding: '12px 16px', marginBottom: 24, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: C.critical, fontSize: 14, fontWeight: 600 }}>
              <AlertTriangle size={16} /> {error}
            </div>
            <button onClick={() => setError('')} style={{ background: 'none', border: 'none', cursor: 'pointer' }}><X size={16} color={C.critical} /></button>
          </div>
        )}

        <AnimatePresence mode="wait">
          {/* ─── STEP 1 ─── */}
          {step === 1 && (
            <motion.div key="s1" variants={pageV} initial="enter" animate="center" exit="exit" transition={{ duration: 0.3 }}>
              <div style={{ background: 'white', borderRadius: 24, border: `1px solid ${C.border}`, overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
                <div style={{ background: `linear-gradient(135deg, ${C.primaryLight}, white)`, padding: '24px 32px', borderBottom: `1px solid ${C.border}`, display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{ width: 42, height: 42, background: 'rgba(10,110,138,0.1)', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <User size={22} color={C.primary} />
                  </div>
                  <div>
                    <h2 style={{ fontSize: 20, fontWeight: 700, color: C.text, margin: 0 }}>Patient Intake</h2>
                    <p style={{ fontSize: 13, color: C.textMuted, margin: 0 }}>Step 1 of 4 — Basic demographics and health history</p>
                  </div>
                </div>
                <div style={{ padding: 32 }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                    <div>
                      <label style={{ display: 'block', fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 6 }}>Full Name *</label>
                      <input type="text" value={patientInfo.name} onChange={e => setPatientInfo({ ...patientInfo, name: e.target.value })} placeholder="Enter patient name" style={inputStyle} />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 6 }}>Age *</label>
                      <input type="number" min="1" max="120" value={patientInfo.age} onChange={e => setPatientInfo({ ...patientInfo, age: e.target.value })} placeholder="Age" style={inputStyle} />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 6 }}>Gender *</label>
                      <select value={patientInfo.gender} onChange={e => setPatientInfo({ ...patientInfo, gender: e.target.value })} style={inputStyle}>
                        <option value="">Select gender</option>
                        <option value="Male">Male</option>
                        <option value="Female">Female</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 6 }}>Contact Number</label>
                      <input type="tel" value={patientInfo.contact} onChange={e => setPatientInfo({ ...patientInfo, contact: e.target.value })} placeholder="+91-XXXXX-XXXXX" style={inputStyle} />
                    </div>
                    <div style={{ gridColumn: 'span 2' }}>
                      <label style={{ display: 'block', fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 6 }}>Known Medical History</label>
                      <textarea rows={3} value={patientInfo.medical_history} onChange={e => setPatientInfo({ ...patientInfo, medical_history: e.target.value })} placeholder="e.g., Asthma, Diabetes, Hypertension, past surgeries..." style={{ ...inputStyle, resize: 'none' }} />
                    </div>
                  </div>
                  <div style={{ marginTop: 32, display: 'flex', justifyContent: 'flex-end' }}>
                    <button onClick={() => {
                      if (!patientInfo.name.trim() || !patientInfo.age || !patientInfo.gender) { setError('Please fill in name, age, and gender.'); return; }
                      setError(''); setStep(2);
                    }} style={btnPrimary}>
                      Continue to Symptoms <ArrowRight size={16} />
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* ─── STEP 2 ─── */}
          {step === 2 && (
            <motion.div key="s2" variants={pageV} initial="enter" animate="center" exit="exit" transition={{ duration: 0.3 }}>
              <div style={{ background: 'white', borderRadius: 24, border: `1px solid ${C.border}`, overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
                <div style={{ background: `linear-gradient(135deg, ${C.primaryLight}, white)`, padding: '24px 32px', borderBottom: `1px solid ${C.border}`, display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{ width: 42, height: 42, background: 'rgba(10,110,138,0.1)', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Stethoscope size={22} color={C.primary} />
                  </div>
                  <div>
                    <h2 style={{ fontSize: 20, fontWeight: 700, color: C.text, margin: 0 }}>Symptom Assessment & Lab Reports</h2>
                    <p style={{ fontSize: 13, color: C.textMuted, margin: 0 }}>Step 2 of 4 — Select symptoms and upload lab results</p>
                  </div>
                </div>
                <div style={{ padding: 32 }}>
                  {/* Symptom Selector */}
                  <div style={{ marginBottom: 32 }}>
                    <h3 style={{ fontSize: 15, fontWeight: 700, color: C.text, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                      <ClipboardList size={18} color={C.primary} /> Select Your Symptoms
                    </h3>
                    <div style={{ position: 'relative', marginBottom: 12 }}>
                      <Search size={16} color={C.textMuted} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }} />
                      <input type="text" value={symptomSearch} onChange={e => setSymptomSearch(e.target.value)} placeholder="Search symptoms..." style={{ ...inputStyle, paddingLeft: 36 }} />
                    </div>
                    {selectedSymptoms.length > 0 && (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 12 }}>
                        {selectedSymptoms.map(s => (
                          <span key={s} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, background: C.primary, color: 'white', fontSize: 12, fontWeight: 600, padding: '6px 12px', borderRadius: 8 }}>
                            {s.replace(/_/g, ' ')}
                            <button onClick={() => setSelectedSymptoms(selectedSymptoms.filter(x => x !== s))} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}><X size={12} color="white" /></button>
                          </span>
                        ))}
                      </div>
                    )}
                    <div style={{ maxHeight: 200, overflowY: 'auto', display: 'flex', flexWrap: 'wrap', gap: 6, padding: 12, background: C.bg, borderRadius: 12, border: `1px solid ${C.border}` }}>
                      {(symptomSearch ? filteredSymptoms : allSymptoms.slice(0, 60)).map(s => (
                        <SymptomTag key={s} symptom={s} selected={selectedSymptoms.includes(s)} onClick={() => {
                          if (selectedSymptoms.includes(s)) setSelectedSymptoms(selectedSymptoms.filter(x => x !== s));
                          else setSelectedSymptoms([...selectedSymptoms, s]);
                        }} />
                      ))}
                    </div>
                  </div>

                  {/* Description */}
                  <div style={{ marginBottom: 32 }}>
                    <h3 style={{ fontSize: 15, fontWeight: 700, color: C.text, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Activity size={18} color={C.primary} /> Describe Your Symptoms
                    </h3>
                    <textarea rows={4} value={symptomDescription} onChange={e => setSymptomDescription(e.target.value)}
                      placeholder="Describe symptoms in detail: onset, severity, duration, what makes it worse or better..."
                      style={{ ...inputStyle, resize: 'none' }} />
                  </div>

                  {/* Lab Upload */}
                  <div style={{ marginBottom: 32 }}>
                    <h3 style={{ fontSize: 15, fontWeight: 700, color: C.text, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Microscope size={18} color={C.primary} /> Lab Report Scanner (Optional)
                    </h3>
                    <div style={{ border: `2px dashed ${C.border}`, borderRadius: 16, padding: 24, textAlign: 'center', background: C.bg, cursor: 'pointer', transition: 'border-color 0.2s' }}>
                      <input type="file" accept=".png,.jpg,.jpeg,.pdf" onChange={handleLabUpload} style={{ display: 'none' }} id="lab-upload" />
                      <label htmlFor="lab-upload" style={{ cursor: 'pointer' }}>
                        {uploading ? (
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, color: C.primary }}>
                            <Loader2 size={20} className="animate-spin" /> Processing lab report...
                          </div>
                        ) : (
                          <>
                            <Upload size={32} color={C.textMuted} style={{ margin: '0 auto 8px' }} />
                            <p style={{ fontSize: 14, fontWeight: 600, color: C.textSec }}>Upload Lab PDF or Image</p>
                            <p style={{ fontSize: 12, color: C.textMuted, marginTop: 4 }}>PNG, JPG, or PDF — AI will extract key metrics</p>
                          </>
                        )}
                      </label>
                    </div>
                    {labReportText && (
                      <div style={{ marginTop: 12, background: C.successBg, border: `1px solid rgba(56,161,105,0.2)`, borderRadius: 12, padding: 16 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: C.success, fontSize: 13, fontWeight: 700, marginBottom: 8 }}>
                          <CheckCircle size={16} /> Lab report extracted successfully
                        </div>
                        <p style={{ fontSize: 12, color: C.textSec, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical' }}>{labReportText}</p>
                      </div>
                    )}
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <button onClick={() => setStep(1)} style={btnSecondary}><ArrowLeft size={16} /> Back</button>
                    <button onClick={handleGenerateQuestionnaire} disabled={generating} style={{ ...btnPrimary, opacity: generating ? 0.6 : 1 }}>
                      {generating ? <><Loader2 size={16} className="animate-spin" /> Running ML Pass 1...</> : <>Run ML Pass 1 & Build Questions <ArrowRight size={16} /></>}
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* ─── STEP 3 ─── */}
          {step === 3 && (
            <motion.div key="s3" variants={pageV} initial="enter" animate="center" exit="exit" transition={{ duration: 0.3 }}>
              <div style={{ background: 'white', borderRadius: 24, border: `1px solid ${C.border}`, overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
                <div style={{ background: `linear-gradient(135deg, ${C.primaryLight}, white)`, padding: '24px 32px', borderBottom: `1px solid ${C.border}`, display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{ width: 42, height: 42, background: 'rgba(10,110,138,0.1)', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Brain size={22} color={C.primary} />
                  </div>
                  <div>
                    <h2 style={{ fontSize: 20, fontWeight: 700, color: C.text, margin: 0 }}>LLM-Generated Follow-up Questionnaire</h2>
                    <p style={{ fontSize: 13, color: C.textMuted, margin: 0 }}>Step 3 of 4 — Select one answer. Supported symptoms found in your answer are passed to ML.</p>
                  </div>
                </div>

                {questionnaire.length > 0 && (
                  <div style={{ padding: '24px 32px 0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <span style={{ fontSize: 12, fontWeight: 700, color: C.textMuted }}>Question {currentQ + 1} of {questionnaire.length}</span>
                      <span style={{ fontSize: 12, fontWeight: 600, color: C.primary, background: C.primaryLight, padding: '4px 12px', borderRadius: 999 }}>
                        Select one answer
                      </span>
                    </div>
                    <div style={{ width: '100%', background: '#F1F5F9', borderRadius: 999, height: 8 }}>
                      <div style={{ width: `${((currentQ + 1) / questionnaire.length) * 100}%`, background: `linear-gradient(135deg, ${C.primary}, ${C.teal})`, height: 8, borderRadius: 999, transition: 'width 0.5s' }} />
                    </div>
                  </div>
                )}

                <div style={{ padding: 32 }}>
                  {questionnaire.length > 0 && currentQ < questionnaire.length && (
                    <AnimatePresence mode="wait">
                      <motion.div key={currentQ} initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -30 }} transition={{ duration: 0.25 }}>
                        <h3 style={{ fontSize: 18, fontWeight: 700, color: C.text, marginBottom: 24 }}>
                          {questionnaire[currentQ].question_text}
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                          {(questionnaire[currentQ].options || []).map(option => {
                            const selected = questionnaireAnswers[questionnaire[currentQ].question_id] === option;
                            return <label key={option} style={{ width: '100%', padding: '15px 18px', borderRadius: 12, cursor: 'pointer', display: 'flex', gap: 12, alignItems: 'center', border: `2px solid ${selected ? C.primary : C.border}`, background: selected ? C.primaryLight : C.bg, color: selected ? C.primaryDark : C.textSec, fontSize: 14, fontWeight: 600 }}>
                              <input type="radio" name={questionnaire[currentQ].question_id} checked={selected} onChange={() => selectQuestionAnswer(questionnaire[currentQ], option)} style={{ accentColor: C.primary }} />
                              {option}
                            </label>;
                          })}
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 32 }}>
                          <button onClick={() => currentQ > 0 ? setCurrentQ(currentQ - 1) : setStep(2)} style={btnSecondary}>
                            <ArrowLeft size={16} /> {currentQ === 0 ? 'Back to Symptoms' : 'Previous'}
                          </button>
                          {currentQ < questionnaire.length - 1 ? (
                            <button onClick={() => {
                              if (!String(questionnaireAnswers[questionnaire[currentQ].question_id] || '').trim()) { setError('Please select an answer before continuing.'); return; }
                              setError(''); setCurrentQ(currentQ + 1);
                            }} style={btnPrimary}>
                              Next Question <ArrowRight size={16} />
                            </button>
                          ) : (
                            <button onClick={() => {
                              if (!String(questionnaireAnswers[questionnaire[currentQ].question_id] || '').trim()) { setError('Please select an answer before continuing.'); return; }
                              setError(''); handleAnalyze();
                            }} disabled={analyzing} style={{ ...btnPrimary, background: `linear-gradient(135deg, ${C.accentDark}, ${C.accent})`, opacity: analyzing ? 0.6 : 1 }}>
                              {analyzing ? <><Loader2 size={16} className="animate-spin" /> Running ML Pass 2...</> : <>Run Final ML Prediction <Brain size={16} /></>}
                            </button>
                          )}
                        </div>
                      </motion.div>
                    </AnimatePresence>
                  )}

                  {analyzing && (
                    <div style={{ textAlign: 'center', padding: '48px 0' }}>
                      <Loader2 size={48} color={C.primary} className="animate-spin" style={{ margin: '0 auto 16px' }} />
                      <h3 style={{ fontSize: 18, fontWeight: 700, color: C.text, marginBottom: 8 }}>Running ML Pass 2</h3>
                      <p style={{ fontSize: 14, color: C.textMuted }}>Combining initial and newly confirmed symptoms through the same trained model...</p>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}

          {/* ─── STEP 4 ─── */}
          {step === 4 && results && (
            <motion.div key="s4" variants={pageV} initial="enter" animate="center" exit="exit" transition={{ duration: 0.3 }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
                {/* Emergency */}
                {results.is_emergency && (
                  <div style={{ background: C.criticalBg, border: `2px solid ${C.critical}`, borderRadius: 20, padding: 24 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: C.critical, fontSize: 18, fontWeight: 800, marginBottom: 8 }}>
                      <AlertTriangle size={24} /> EMERGENCY TRIAGE ALERT
                    </div>
                    <p style={{ fontSize: 14, color: '#991B1B' }}>{results.emergency_instructions}</p>
                    <a href="tel:108" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: C.critical, color: 'white', padding: '10px 24px', borderRadius: 12, fontSize: 14, fontWeight: 700, marginTop: 16 }}>
                      <Phone size={16} /> Call Emergency (108)
                    </a>
                  </div>
                )}

                {/* Primary Diagnosis */}
                <div style={{ background: 'white', borderRadius: 24, border: `1px solid ${C.border}`, overflow: 'hidden', borderLeft: `5px solid ${C.primary}` }}>
                  <div style={{ padding: 32 }}>
                    <div style={{ fontSize: 11, fontWeight: 800, color: C.textMuted, letterSpacing: 2, textTransform: 'uppercase', marginBottom: 8 }}>Primary Screening Classification</div>
                    <h2 style={{ fontSize: 32, fontWeight: 800, color: C.primaryDark, marginBottom: 16 }}>{results.primary_pathology}</h2>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center' }}>
                      <span style={{
                        display: 'inline-flex', alignItems: 'center', gap: 6, padding: '6px 16px', borderRadius: 999, fontSize: 12, fontWeight: 700,
                        background: C.primaryLight,
                        color: C.primary,
                        border: '1px solid rgba(10,110,138,0.2)',
                      }}>
                        <Activity size={14} /> {(results.model_confidence * 100).toFixed(2)}% Model Confidence
                      </span>
                      <span style={{
                        display: 'inline-flex', alignItems: 'center', gap: 6, padding: '6px 16px', borderRadius: 999, fontSize: 12, fontWeight: 700,
                        background: ['CRITICAL', 'HIGH'].includes(results.triage_level) ? C.criticalBg : results.triage_level === 'MEDIUM' ? C.amberBg : C.successBg,
                        color: ['CRITICAL', 'HIGH'].includes(results.triage_level) ? C.critical : results.triage_level === 'MEDIUM' ? C.amber : C.success,
                      }}>
                        <Shield size={14} /> {results.triage_level}
                      </span>
                      <span style={{ fontSize: 13, color: C.textMuted }}>Patient: <b>{patientInfo.name}</b> · {patientInfo.age} yrs, {patientInfo.gender}</span>
                    </div>
                  </div>
                </div>

                {results.three_way_comparison && (() => {
                  const comparison = results.three_way_comparison;
                  const llm = comparison.llm_only || {};
                  const ml = comparison.ml_only || {};
                  const hybrid = comparison.hybrid_ml_llm || {};
                  return <div style={{ background: 'white', borderRadius: 20, border: `1px solid ${C.border}`, padding: 28 }}>
                    <h3 style={{ fontSize: 18, fontWeight: 800, color: C.text, marginBottom: 6 }}>Three-Way Research Comparison</h3>
                    <p style={{ fontSize: 13, color: C.textSec, lineHeight: 1.6, marginBottom: 18 }}>All methods receive the same initial case. Only the Hybrid path additionally uses symptoms confirmed in the questionnaire.</p>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 16 }}>
                      <div style={{ background: C.bg, borderRadius: 14, padding: 16 }}>
                        <div style={{ fontSize: 12, fontWeight: 800, color: C.primary, marginBottom: 8 }}>LLM-ONLY</div>
                        <b style={{ color: C.text }}>{llm.most_likely_condition || 'Abstained / insufficient information'}</b>
                        <PredictionList predictions={llm.ranked_conditions} kind="llm" />
                        <p style={{ fontSize: 11, color: C.textMuted, lineHeight: 1.5 }}>{llm.confidence_label}</p>
                        <p style={{ fontSize: 12, color: C.textSec }}>Severity: <b>{llm.severity || 'UNKNOWN'}</b></p>
                      </div>
                      <div style={{ background: C.bg, borderRadius: 14, padding: 16 }}>
                        <div style={{ fontSize: 12, fontWeight: 800, color: C.primary, marginBottom: 8 }}>ML-ONLY</div>
                        <b style={{ color: C.text }}>{ml.summary?.top_prediction || 'Insufficient evidence'}</b>
                        <PredictionList predictions={ml.predictions} />
                        <p style={{ fontSize: 11, color: C.textMuted, lineHeight: 1.5 }}>{ml.summary?.confidence_label}</p>
                        <p style={{ fontSize: 12, color: C.textSec }}>Severity: <b>{ml.severity || 'UNKNOWN'}</b></p>
                      </div>
                      <div style={{ background: C.primaryLight, borderRadius: 14, padding: 16 }}>
                        <div style={{ fontSize: 12, fontWeight: 800, color: C.primary, marginBottom: 8 }}>HYBRID ML + LLM</div>
                        <b style={{ color: C.text }}>{hybrid.summary?.top_prediction || 'Insufficient evidence'}</b>
                        <PredictionList predictions={hybrid.final_predictions} />
                        <p style={{ fontSize: 12, color: C.textSec }}>Confidence change: <b>{hybrid.confidence_change_percentage_points >= 0 ? '+' : ''}{hybrid.confidence_change_percentage_points || 0} pp</b></p>
                        <p style={{ fontSize: 12, color: C.textSec }}>Severity: <b>{hybrid.severity || 'UNKNOWN'}</b></p>
                      </div>
                    </div>
                    <div style={{ marginTop: 16, background: C.amberBg, borderRadius: 12, padding: 12, fontSize: 13, color: '#92400E' }}>
                      <b>Agreement: </b>{(comparison.agreement?.status || 'disagreement').replace(/_/g, ' ')}. LLM: {comparison.agreement?.leading_predictions?.llm_only || 'abstained'}; ML: {comparison.agreement?.leading_predictions?.ml_only || 'uncertain'}; Hybrid: {comparison.agreement?.leading_predictions?.hybrid_ml_llm || 'uncertain'}.
                    </div>
                  </div>;
                })()}

                {/* Pass 1 vs Pass 2 */}
                <div style={{ background: 'white', borderRadius: 20, border: `1px solid ${C.border}`, padding: 28 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 700, color: C.text, marginBottom: 6 }}>How the Model Ranking Changed</h3>
                  <p style={{ fontSize: 13, color: C.textSec, lineHeight: 1.6, marginBottom: 18 }}>
                    Pass 1 is the preliminary ranking from the initially reported symptoms. Pass 2 reruns the same ML model after adding symptoms confirmed through the questionnaire. These percentages are model confidence scores, not real-world probabilities of disease.
                  </p>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                    {[
                      ['Pass 1 — initial symptom ranking', results.pass1_predictions],
                      ['Pass 2 — updated final ranking', results.pass2_predictions],
                    ].map(([label, predictions]) => (
                      <div key={label} style={{ background: C.bg, borderRadius: 14, padding: 18 }}>
                        <div style={{ fontSize: 12, fontWeight: 800, color: C.textMuted, textTransform: 'uppercase', marginBottom: 10 }}>{label}</div>
                        {(predictions || []).slice(0, 3).map((item, index) => (
                          <div key={item.disease} style={{ display: 'flex', justifyContent: 'space-between', gap: 12, padding: '5px 0', fontSize: 13, color: C.textSec }}>
                            <span>{index + 1}. {item.disease}</span>
                            <b>{(item.model_confidence * 100).toFixed(2)}%</b>
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                  <p style={{ fontSize: 12, color: C.textMuted, marginTop: 14 }}><b>New symptoms added in Pass 2:</b> {(results.evidence?.questionnaire_positive || []).map(s => s.replace(/_/g, ' ')).join(', ') || 'None'}. Unchecked options were treated as unknown, not absent.</p>
                </div>

                {/* Details Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                  <div style={{ background: 'white', borderRadius: 20, border: `1px solid ${C.border}`, padding: 28, gridColumn: '1 / -1' }}>
                    <h3 style={{ fontSize: 15, fontWeight: 700, color: C.text, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Brain size={18} color={C.primary} /> What is {results.primary_pathology}?
                    </h3>
                    <div style={{ background: C.primaryLight, borderRadius: 12, padding: '14px 18px', marginBottom: 16 }}>
                      <p style={{ fontSize: 14, color: C.primaryDark, lineHeight: 1.7, margin: 0 }}>
                        {results.condition_definition || results.condition_information?.definition || 'A condition definition is not available.'}
                      </p>
                    </div>
                    <div style={{ fontSize: 12, fontWeight: 800, color: C.textMuted, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>Model explanation</div>
                    <p style={{ fontSize: 14, color: C.textSec, lineHeight: 1.7, whiteSpace: 'pre-line' }}>{results.clinical_reasoning_summary}</p>
                  </div>

                  <div style={{ background: 'white', borderRadius: 20, border: `1px solid ${C.border}`, padding: 28 }}>
                    <h3 style={{ fontSize: 15, fontWeight: 700, color: C.text, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Activity size={18} color={C.primary} /> Other Model Candidates (Pass 2)
                    </h3>
                    <p style={{ fontSize: 12, color: C.textMuted, lineHeight: 1.5, marginBottom: 8 }}>
                      These are lower-ranked alternatives from the model, not confirmed differential diagnoses.
                    </p>
                    {results.differential_diagnoses?.map((d, i) => (
                      <div key={d.name || d.disease || i} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, color: C.textSec, padding: '6px 0' }}>
                        <div style={{ width: 6, height: 6, borderRadius: '50%', background: C.primary, flexShrink: 0 }} />
                        <span style={{ flex: 1 }}>{i + 2}. {d.name || d.disease}</span>
                        <b>{(d.model_confidence * 100).toFixed(2)}%</b>
                      </div>
                    ))}
                  </div>

                  <div style={{ background: 'white', borderRadius: 20, border: `1px solid ${C.border}`, padding: 28 }}>
                    <h3 style={{ fontSize: 15, fontWeight: 700, color: C.text, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Stethoscope size={18} color={C.primary} /> Recommended Specialist
                    </h3>
                    <div style={{ background: C.primaryLight, borderRadius: 12, padding: '12px 20px', display: 'inline-block' }}>
                      <span style={{ color: C.primaryDark, fontWeight: 700 }}>{results.suggested_clinical_path}</span>
                    </div>
                  </div>

                  <div style={{ background: 'white', borderRadius: 20, border: `1px solid ${C.border}`, padding: 28 }}>
                    <h3 style={{ fontSize: 15, fontWeight: 700, color: C.text, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Shield size={18} color={C.primary} /> Precautionary Measures
                    </h3>
                    {(results.precautionary_countermeasures || []).map((p, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, fontSize: 14, color: C.textSec, padding: '4px 0' }}>
                        <CheckCircle size={16} color={C.success} style={{ marginTop: 2, flexShrink: 0 }} /> {p}
                      </div>
                    ))}
                    {results.precaution_notice && (
                      <p style={{ fontSize: 11, color: C.textMuted, lineHeight: 1.5, marginTop: 10 }}>{results.precaution_notice}</p>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16 }}>
                  <button onClick={handleDownloadPDF} style={btnPrimary}><Download size={16} /> Download Clinical Report PDF</button>
                  <button onClick={startOver} style={btnSecondary}><RefreshCw size={16} /> Start New Screening</button>
                </div>

                <div style={{ background: C.amberBg, border: `1px solid rgba(214,158,46,0.2)`, borderRadius: 12, padding: 16, fontSize: 12, color: '#92400E' }}>
                  <b>Disclaimer:</b> This is an educational/research prototype, not a diagnosis. Model confidence is not clinical certainty or real-world disease probability.
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
