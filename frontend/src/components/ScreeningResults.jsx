import { useState } from 'react';
import { ArrowRight, AlertTriangle, Check, ChevronDown, ClipboardList, Download, FileText, Info, RefreshCw, Shield, Stethoscope } from 'lucide-react';
import './ScreeningResults.css';

const URGENCY = { routine: 'Routine review', prompt: 'Prompt review suggested', emergency: 'Seek emergency assessment', unclear: 'Urgency needs clarification' };

function Facts({ ids, evidence }) {
  return <div className="sr-facts">{[...new Set(ids)].map(id => {
    const item = evidence.find(fact => fact.id === id);
    return item && <div className="sr-fact" key={id}><span className="sr-fact-id">{id}</span><div><span>{item.label}</span><p>{item.text}</p></div></div>;
  })}</div>;
}

function Possibility({ condition, evidence, index }) {
  return <details className="sr-alternative">
    <summary><span className="sr-number">{String(index + 1).padStart(2, '0')}</span><div><h4>{condition.name}</h4><span>View supporting facts and limitations</span></div><ChevronDown size={18} className="sr-chevron" /></summary>
    <div className="sr-alternative-body"><p>{condition.overview}</p><h5>Why it could fit</h5><p>{condition.explanation}</p><Facts ids={condition.evidence_ids} evidence={evidence} /><h5>What remains unconfirmed</h5><ul>{condition.uncertainties.map((item, i) => <li key={i}>{item}</li>)}</ul></div>
  </details>;
}

export default function ScreeningResults({ results, patientInfo, questionnaire, questionnaireAnswers, selectedSymptoms, downloading, onDownload, onReset }) {
  const [view, setView] = useState('assessment');
  const insufficient = results.status === 'insufficient_evidence';
  const urgent = ['prompt', 'emergency'].includes(results.urgency);
  const evidence = results.evidence;
  const unknownCount = Object.values(questionnaireAnswers).filter(answer => /^(not sure|none of these)$/i.test(answer)).length;
  return <div className="sr-root">
    <div className="sr-topline"><span><Check size={14} /> Screening complete</span><span>PERSONAL HEALTH SUMMARY</span></div>
    <header className="sr-header"><div><p className="sr-eyebrow">A clearer picture of your symptoms</p><h2>Your screening, explained.</h2><p>For {patientInfo.name} <span>·</span> {patientInfo.age} years <span>·</span> {patientInfo.gender}</p></div><button className="sr-download" disabled={downloading} onClick={onDownload}><Download size={17} />{downloading ? 'Preparing report…' : 'Download report'}</button></header>
    <div className="sr-context-strip"><span><ClipboardList size={16} /><b>{questionnaire.length}</b> follow-up answers</span><span><Stethoscope size={16} /><b>{selectedSymptoms.length}</b> selected symptoms</span><span><Info size={16} />{unknownCount ? `${unknownCount} answers need clarification` : 'Review your reported facts below'}</span></div>
    {results.urgency === 'emergency' && <div className="sr-emergency" role="alert"><AlertTriangle size={23} /><div><h3>Seek emergency assessment</h3><p>{results.urgency_reason}</p></div></div>}
    <div className="sr-view-switch" aria-label="Result view"><button aria-pressed={view === 'assessment'} onClick={() => setView('assessment')}>Assessment overview</button><button aria-pressed={view === 'evidence'} onClick={() => setView('evidence')}>Information used <span>{evidence.length}</span></button></div>
    <div className="sr-layout"><div className="sr-main">
      {view === 'assessment' ? <>
        <section className={`sr-outcome ${insufficient ? 'sr-outcome-uncertain' : ''}`}><div className="sr-outcome-label"><span className="sr-icon"><Stethoscope size={21} /></span><span>{insufficient ? 'MORE INFORMATION NEEDED' : 'MAIN POSSIBILITY'}</span><span className="sr-support">{insufficient ? 'Not enough evidence' : results.certainty === 'low' ? 'Tentative suggestion' : 'Possible explanation'}</span></div><h3>{insufficient ? 'Insufficient evidence' : results.primary_condition.name}</h3><p>{results.summary}</p><div className="sr-outcome-note"><Info size={16} /><span>{insufficient ? 'The available information does not support a useful leading explanation yet.' : 'A screening suggestion, not a confirmed diagnosis. An examination or tests may change this assessment.'}</span></div></section>
        {results.primary_condition && <section className="sr-panel"><div className="sr-section-heading"><span className="sr-section-icon"><FileText size={18} /></span><div><h3>Why this possibility was suggested</h3><p>Connecting your reported facts to the explanation.</p></div></div><p className="sr-overview">{results.primary_condition.overview}</p><p>{results.primary_condition.explanation}</p><h4 className="sr-small-heading">Supporting information you provided</h4><Facts ids={results.primary_condition.evidence_ids} evidence={evidence} /><div className="sr-limitations"><h4>What this does not confirm</h4><ul>{results.primary_condition.uncertainties.map((item, i) => <li key={i}>{item}</li>)}</ul></div></section>}
        {results.other_possibilities.length > 0 && <section className="sr-panel"><div className="sr-section-heading"><span className="sr-section-icon"><ClipboardList size={18} /></span><div><h3>Other possibilities</h3><p>Different conditions can share the same symptoms.</p></div></div>{results.other_possibilities.map((condition, i) => <Possibility key={i} condition={condition} index={i} evidence={evidence} />)}</section>}
        <section className="sr-panel"><div className="sr-section-heading"><span className="sr-section-icon sr-amber"><Info size={18} /></span><div><h3>What is still uncertain</h3><p>The gaps that a follow-up assessment can help resolve.</p></div></div><p>{results.uncertainty_explanation}</p>{results.missing_information.length > 0 && <ul className="sr-missing">{results.missing_information.map((item, i) => <li key={i}>{item}</li>)}</ul>}</section>
      </> : <section className="sr-panel"><div className="sr-section-heading"><span className="sr-section-icon"><ClipboardList size={18} /></span><div><h3>The information behind your screening</h3><p>Your original context and follow-up answers, without inferred findings.</p></div></div><Facts ids={evidence.map(item => item.id)} evidence={evidence} /><p className="sr-model">Generated by {results.model}. Evidence links show which facts were cited; they do not verify medical correctness.</p></section>}
    </div><aside className="sr-sidebar">
      <section className={`sr-panel sr-next ${urgent ? 'sr-next-urgent' : ''}`}><div className="sr-section-heading"><span className="sr-section-icon"><ArrowRight size={18} /></span><h3>Your next steps</h3></div><div className="sr-urgency"><Shield size={16} />{URGENCY[results.urgency]}</div><p>{results.urgency_reason}</p><ol>{results.next_steps.map((item, i) => <li key={i}><span>{i + 1}</span><p>{item}</p></li>)}</ol><p className="sr-caption">Urgency is AI guidance, not a validated triage score.</p></section>
      {results.warning_signs.length > 0 && <section className="sr-panel sr-warning"><div className="sr-section-heading"><AlertTriangle size={19} /><h3>Watch for changes</h3></div><ul>{results.warning_signs.map((item, i) => <li key={i}>{item}</li>)}</ul></section>}
      <section className="sr-report-card"><FileText size={25} /><h3>Take the explanation with you.</h3><p>Your PDF includes the assessment, supporting facts, uncertainties, and next steps to discuss with a professional.</p><button disabled={downloading} onClick={onDownload}><Download size={16} />{downloading ? 'Preparing…' : 'Download explainable PDF'}</button></section>
    </aside></div>
    <footer className="sr-footer"><p><Info size={18} /><span>{results.medical_disclaimer}</span></p><button onClick={onReset}><RefreshCw size={16} />Start a new screening</button></footer>
  </div>;
}
