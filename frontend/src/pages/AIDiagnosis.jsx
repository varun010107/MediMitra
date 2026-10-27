import { useState } from 'react';
import { usePatient } from '../context/PatientContext';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import ScreeningResults from '../components/ScreeningResults';
import { SYMPTOM_GROUPS } from '../data/symptoms';
import {
  User, Stethoscope, Brain, FileText, ArrowRight, ArrowLeft,
  Upload, Search, CheckCircle, AlertTriangle, X, Loader2,
  Activity, Microscope, ClipboardList,
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
            padding: '8px clamp(8px, 2vw, 18px)', borderRadius: 999, fontSize: 13, fontWeight: 700,
            background: s.id < current ? C.success : s.id === current ? C.primary : '#F1F5F9',
            color: s.id <= current ? 'white' : C.textMuted,
            boxShadow: s.id === current ? '0 4px 14px rgba(10,110,138,0.3)' : 'none',
            transition: 'all 0.3s',
          }}>
            {s.id < current ? <CheckCircle size={16} /> : <s.icon size={16} />}
            <span className="hidden sm:inline">{s.label}</span>
          </div>
          {i < STEPS.length - 1 && (
            <div style={{ width: 'clamp(12px, 4vw, 32px)', height: 2, margin: '0 4px', background: s.id < current ? C.success : '#E2E8F0' }} />
          )}
        </div>
      ))}
    </div>
  );
}

function SymptomTag({ symptom, selected, onClick }) {
  return (
    <button onClick={onClick} aria-pressed={selected} style={{
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

function errorMessage(error, fallback) {
  const detail = error.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map(item => item.msg).join('. ');
  return detail?.message || fallback;
}

export default function AIDiagnosis() {
  const {
    patientInfo, setPatientInfo, selectedSymptoms, setSelectedSymptoms,
    symptomDescription, setSymptomDescription, labReportText, setLabReportText,
    questionnaire, setQuestionnaire, questionnaireAnswers, setQuestionnaireAnswers,
    results, setResults, reset,
  } = usePatient();

  const [step, setStep] = useState(1);
  const [symptomGroup, setSymptomGroup] = useState('All');
  const [additionalDetails, setAdditionalDetails] = useState('');
  const [downloading, setDownloading] = useState(false);
  const [symptomSearch, setSymptomSearch] = useState('');
  const [uploading, setUploading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const [currentQ, setCurrentQ] = useState(0);

  const visibleGroups = SYMPTOM_GROUPS.filter(group => symptomGroup === 'All' || group.name === symptomGroup).map(group => ({ ...group, symptoms: group.symptoms.filter(symptom => symptom.toLowerCase().includes(symptomSearch.toLowerCase())) })).filter(group => group.symptoms.length > 0);

  const selectQuestionAnswer = (question, answer) => {
    setQuestionnaireAnswers({ ...questionnaireAnswers, [question.question_id]: answer });
  };

  const handleLabUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true); setError('');
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
        lab_report_text: labReportText || null,
      });
      setQuestionnaire(data.questions); setQuestionnaireAnswers({}); setResults(null); setAdditionalDetails(''); setCurrentQ(0); setStep(3);
    } catch (err) {
      setError(errorMessage(err, 'Failed to generate questionnaire.'));
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
        lab_report_text: labReportText || null,
        questionnaire_answers: questionnaireAnswers,
        additional_details: additionalDetails,
        questionnaire,
      });
      setResults(data); setStep(4);
    } catch (err) {
      setError(errorMessage(err, 'Analysis failed.'));
    }
    setAnalyzing(false);
  };

  const handleDownloadPDF = async () => {
    setDownloading(true); setError('');
    try {
      const response = await axios.post('/api/generate-pdf', {
        patient_name: patientInfo.name, age: parseInt(patientInfo.age),
        gender: patientInfo.gender, medical_history: patientInfo.medical_history, results,
      }, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement('a');
      a.href = url; a.download = 'MediMitra_Screening_Report.pdf'; document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => window.URL.revokeObjectURL(url), 1000);
    } catch { setError('Failed to generate PDF. Please try again.'); }
    finally { setDownloading(false); }
  };

  const startOver = () => { reset(); setAdditionalDetails(''); setStep(1); setError(''); setCurrentQ(0); };

  const pageV = { enter: { opacity: 0, x: 50 }, center: { opacity: 1, x: 0 }, exit: { opacity: 0, x: -50 } };

  return (
    <div style={{ paddingTop: 72, minHeight: '100vh', overflowWrap: 'anywhere', background: C.bg }}>
      {/* Header */}
      <section style={{ background: `linear-gradient(135deg, ${C.primaryDark}, ${C.primary}, ${C.teal})`, padding: '48px 0' }}>
        <div style={{ maxWidth: 900, margin: '0 auto', padding: '0 24px', textAlign: 'center' }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)',
            borderRadius: 999, padding: '6px 16px', fontSize: 13, color: 'rgba(255,255,255,0.9)', fontWeight: 600, marginBottom: 16,
          }}>
            <Brain size={16} /> Personalized AI Health Screening
          </div>
          <h1 style={{ fontSize: 34, fontWeight: 800, color: 'white' }}>Patient Screening & Care Console</h1>
          <p style={{ color: 'rgba(255,255,255,0.6)', marginTop: 8, fontSize: 14 }}>Questions tailored to your symptoms and history, with clear explanations and uncertainty</p>
        </div>
      </section>

      <div style={{ maxWidth: step === 4 ? 1160 : 900, margin: '0 auto', padding: '32px 24px' }}>
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
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 220px), 1fr))', gap: 20 }}>
                    <div>
                      <label style={{ display: 'block', fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 6 }}>Full Name *</label>
                      <input type="text" value={patientInfo.name} onChange={e => setPatientInfo({ ...patientInfo, name: e.target.value })} placeholder="Enter patient name" style={inputStyle} />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 6 }}>Age *</label>
                      <input type="number" min="0" max="120" value={patientInfo.age} onChange={e => setPatientInfo({ ...patientInfo, age: e.target.value })} placeholder="Age" style={inputStyle} />
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
                    <div style={{ gridColumn: '1 / -1' }}>
                      <label style={{ display: 'block', fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 6 }}>Medical History, Medicines & Allergies</label>
                      <textarea rows={3} value={patientInfo.medical_history} onChange={e => setPatientInfo({ ...patientInfo, medical_history: e.target.value })} placeholder="Include existing conditions, medicines, allergies, recent illness, surgeries, or pregnancy if relevant. Leave blank if unknown." style={{ ...inputStyle, resize: 'none' }} />
                    </div>
                  </div>
                  <p style={{ marginTop: 20, color: C.textSec, fontSize: 12, lineHeight: 1.7 }}>Your health information and any uploaded reports are sent to Google Gemini to prepare this screening. AI output can be wrong and needs professional review.</p>
                  <div style={{ marginTop: 32, display: 'flex', justifyContent: 'flex-end' }}>
                    <button onClick={() => {
                      if (!patientInfo.name.trim() || patientInfo.age === '' || !Number.isInteger(Number(patientInfo.age)) || Number(patientInfo.age) < 0 || Number(patientInfo.age) > 120 || !patientInfo.gender) { setError('Please enter a name, an age from 0 to 120, and gender.'); return; }
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
                    <p style={{ fontSize: 13, color: C.textMuted, margin: 0 }}>Step 2 of 4 — Describe any symptoms in your own words; labs are optional</p>
                  </div>
                </div>
                <div style={{ padding: 32 }}>
                  {/* Symptom Selector */}
                  <div style={{ marginBottom: 32 }}>
                    <h3 style={{ fontSize: 15, fontWeight: 700, color: C.text, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                      <ClipboardList size={18} color={C.primary} /> Common symptoms (optional shortcuts)
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
                    <p style={{ color: C.textSec, fontSize: 12, marginBottom: 12 }}>Choose what you are experiencing. These are shortcuts for describing symptoms, not a list of conditions the AI can diagnose.</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7, marginBottom: 14 }} aria-label="Symptom categories">
                      {['All', ...SYMPTOM_GROUPS.map(group => group.name)].map(name => <button key={name} aria-pressed={symptomGroup === name} onClick={() => setSymptomGroup(name)} style={{ padding: '6px 10px', borderRadius: 20, fontSize: 11, border: `1px solid ${symptomGroup === name ? C.primary : C.border}`, color: symptomGroup === name ? C.primary : C.textSec, background: symptomGroup === name ? C.primaryLight : 'white', cursor: 'pointer' }}>{name}</button>)}
                    </div>
                    <div style={{ maxHeight: 340, overflowY: 'auto', padding: 16, background: C.bg, borderRadius: 12, border: `1px solid ${C.border}` }}>
                      {visibleGroups.map(group => <div key={group.name} style={{ marginBottom: 16 }}>
                        <h4 style={{ fontSize: 11, color: C.textSec, fontWeight: 750, letterSpacing: .5, textTransform: 'uppercase', marginBottom: 9 }}>{group.name}</h4>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7 }}>{group.symptoms.map(symptom => <SymptomTag key={symptom} symptom={symptom} selected={selectedSymptoms.includes(symptom)} onClick={() => setSelectedSymptoms(selectedSymptoms.includes(symptom) ? selectedSymptoms.filter(item => item !== symptom) : [...selectedSymptoms, symptom])} />)}</div>
                      </div>)}
                      {!visibleGroups.length && <p style={{ fontSize: 13, color: C.textSec }}>No matching shortcut. Describe this symptom in your own words below.</p>}
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
                        <p style={{ fontSize: 12, color: C.textSec }}>Review and correct the AI extraction before continuing. It may contain errors.</p>
                        <textarea aria-label="Lab findings" rows={6} value={labReportText} onChange={e => setLabReportText(e.target.value)} style={{ ...inputStyle, marginTop: 8 }} />
                        <button onClick={() => setLabReportText('')} style={{ ...btnSecondary, marginTop: 8 }}>Remove lab context</button>
                      </div>
                    )}
                  </div>

                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, justifyContent: 'space-between' }}>
                    <button onClick={() => setStep(1)} style={btnSecondary}><ArrowLeft size={16} /> Back</button>
                    <button onClick={handleGenerateQuestionnaire} disabled={generating || uploading} style={{ ...btnPrimary, opacity: generating ? 0.6 : 1 }}>
                      {generating ? <><Loader2 size={16} className="animate-spin" /> Preparing your questions...</> : <>Build My Follow-up Questions <ArrowRight size={16} /></>}
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
                    <p style={{ fontSize: 13, color: C.textMuted, margin: 0 }}>Step 3 of 4 — 6–12 questions tailored to your case. Choose “Not sure” when needed.</p>
                  </div>
                </div>

                {questionnaire.length > 0 && (
                  <div style={{ padding: '24px 32px 0' }}>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, justifyContent: 'space-between', marginBottom: 8 }}>
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
                        <p style={{ fontSize: 13, color: C.textSec, marginBottom: 16 }}>Why we ask: {questionnaire[currentQ].purpose}</p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                          {(questionnaire[currentQ].options || []).map(option => {
                            const selected = questionnaireAnswers[questionnaire[currentQ].question_id] === option;
                            return <label key={option} style={{ width: '100%', padding: '15px 18px', borderRadius: 12, cursor: 'pointer', display: 'flex', gap: 12, alignItems: 'center', border: `2px solid ${selected ? C.primary : C.border}`, background: selected ? C.primaryLight : C.bg, color: selected ? C.primaryDark : C.textSec, fontSize: 14, fontWeight: 600 }}>
                              <input type="radio" name={questionnaire[currentQ].question_id} checked={selected} onChange={() => selectQuestionAnswer(questionnaire[currentQ], option)} style={{ accentColor: C.primary }} />
                              {option}
                            </label>;
                          })}
                        </div>

                        {currentQ === questionnaire.length - 1 && <div style={{ marginTop: 20 }}>
                          <label style={{ fontWeight: 700, fontSize: 14 }}>Anything else the AI should know? (optional)</label>
                          <textarea rows={3} value={additionalDetails} onChange={e => setAdditionalDetails(e.target.value)} placeholder="Add details that the choices did not capture." style={{ ...inputStyle, marginTop: 8 }} />
                        </div>}
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, justifyContent: 'space-between', marginTop: 32 }}>
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
                              {analyzing ? <><Loader2 size={16} className="animate-spin" /> Reviewing your information...</> : <>Get My Assessment <Brain size={16} /></>}
                            </button>
                          )}
                        </div>
                      </motion.div>
                    </AnimatePresence>
                  )}

                  {analyzing && (
                    <div style={{ textAlign: 'center', padding: '48px 0' }}>
                      <Loader2 size={48} color={C.primary} className="animate-spin" style={{ margin: '0 auto 16px' }} />
                      <h3 style={{ fontSize: 18, fontWeight: 700, color: C.text, marginBottom: 8 }}>Reviewing Your Complete Case</h3>
                      <p style={{ fontSize: 14, color: C.textMuted }}>Considering your symptoms, medical history, lab context, and every follow-up answer...</p>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}

          {step === 4 && results && (
            <motion.div key="s4" variants={pageV} initial="enter" animate="center" exit="exit" transition={{ duration: 0.3 }}>
              <ScreeningResults results={results} patientInfo={patientInfo} questionnaire={questionnaire} questionnaireAnswers={questionnaireAnswers} selectedSymptoms={selectedSymptoms} downloading={downloading} onDownload={handleDownloadPDF} onReset={startOver} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
