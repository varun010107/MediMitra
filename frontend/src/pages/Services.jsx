import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Brain, Microscope, Stethoscope, FileText, Pill, Phone, ArrowRight, Shield, Activity, Clock, Users, CheckCircle, Sparkles } from 'lucide-react';

const C = {
  primary: '#0A6E8A', primaryDark: '#064E63', primaryLight: '#E8F4F8',
  teal: '#0E7C7B', tealLight: '#E6F7F6',
  text: '#1A202C', textSec: '#4A5568', textMuted: '#A0AEC0',
  bg: '#F0F5F7', border: '#E2E8F0', success: '#38A169',
};

const fadeUp = { hidden: { opacity: 0, y: 30 }, visible: { opacity: 1, y: 0 } };

const services = [
  { icon: Brain, title: 'AI Health Screening', gradient: 'linear-gradient(135deg, #3B82F6, #2563EB)', desc: 'Our AI analyzes your symptoms, medical history, and lab reports to provide accurate preliminary diagnosis. The specially curated questionnaire adapts to your responses for precise results.', features: ['Adaptive AI questionnaire', 'Multi-model fallback', 'Differential diagnosis', 'Confidence scoring'] },
  { icon: Microscope, title: 'Lab Report Analysis', gradient: 'linear-gradient(135deg, #8B5CF6, #7C3AED)', desc: 'Upload your lab reports in any format. Our multimodal AI extracts key biomarkers, identifies abnormal values, and correlates them with your symptoms.', features: ['OCR-powered extraction', 'Abnormal value detection', 'Symptom correlation', 'Trend analysis'] },
  { icon: Stethoscope, title: 'Doctor Consultation', gradient: `linear-gradient(135deg, ${C.teal}, ${C.primary})`, desc: 'Based on your AI screening results, we recommend the right specialist and help you find top-rated doctors in your area.', features: ['Specialist matching', 'Location-based search', 'Rating system', 'Appointment booking'] },
  { icon: FileText, title: 'Clinical Reports', gradient: 'linear-gradient(135deg, #EA580C, #F97316)', desc: "Download comprehensive PDF reports with your complete diagnostic summary, lab correlations, and recommendations — ready to share with your doctor.", features: ['Professional PDF', 'Diagnostic summary', 'Lab correlation', 'Physician sign-off'] },
  { icon: Pill, title: 'Precautionary Guidance', gradient: 'linear-gradient(135deg, #16A34A, #22C55E)', desc: 'Evidence-based precautionary measures, lifestyle recommendations, and wellness tips tailored to your specific condition.', features: ['Condition-specific advice', 'Lifestyle modifications', 'Dietary tips', 'Follow-up scheduling'] },
  { icon: Phone, title: 'Emergency Triage', gradient: 'linear-gradient(135deg, #DC2626, #EF4444)', desc: 'Instant identification of critical conditions with automated emergency routing, SOS capabilities, and nearest ER locator.', features: ['Red-flag detection', 'Emergency routing', 'Nearest ER finder', 'SOS alerts'] },
];

export default function Services() {
  return (
    <div style={{ paddingTop: 72 }}>
      {/* Hero */}
      <section style={{ position: 'relative', background: `linear-gradient(135deg, ${C.primaryDark}, ${C.primary}, ${C.teal})`, padding: '96px 0', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', inset: 0, opacity: 0.1 }}>
          <div style={{ position: 'absolute', top: 40, left: 80, width: 400, height: 400, background: 'white', borderRadius: '50%', filter: 'blur(80px)' }} />
        </div>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 24px', position: 'relative', zIndex: 10, textAlign: 'center' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 999, padding: '6px 16px', fontSize: 13, color: 'rgba(255,255,255,0.9)', fontWeight: 600, marginBottom: 24 }}>
            <Stethoscope size={16} /> Our Services
          </div>
          <h1 style={{ fontSize: 48, fontWeight: 800, color: 'white', marginBottom: 16 }}>Comprehensive Healthcare<br/>At Your Fingertips</h1>
          <p style={{ fontSize: 17, color: 'rgba(255,255,255,0.7)', maxWidth: 600, margin: '0 auto' }}>From AI-powered screening to emergency triage, our platform delivers end-to-end healthcare solutions designed for accuracy and compassion.</p>
        </div>
      </section>

      {/* Services */}
      <section style={{ padding: '80px 0', background: C.bg }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 24px', display: 'flex', flexDirection: 'column', gap: 32 }}>
          {services.map((s, i) => (
            <motion.div key={s.title} initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp}
              style={{ background: 'white', borderRadius: 24, overflow: 'hidden', border: `1px solid ${C.border}`, boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
              <div style={{ display: 'grid', gridTemplateColumns: i % 2 === 0 ? '2fr 3fr' : '3fr 2fr' }}>
                <div style={{ background: s.gradient, padding: 48, display: 'flex', alignItems: 'center', justifyContent: 'center', order: i % 2 === 0 ? 0 : 1 }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ width: 80, height: 80, background: 'rgba(255,255,255,0.2)', backdropFilter: 'blur(12px)', borderRadius: 24, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
                      <s.icon size={40} color="white" />
                    </div>
                    <h3 style={{ fontSize: 24, fontWeight: 800, color: 'white' }}>{s.title}</h3>
                  </div>
                </div>
                <div style={{ padding: 40, order: i % 2 === 0 ? 1 : 0 }}>
                  <p style={{ color: C.textSec, lineHeight: 1.7, marginBottom: 24 }}>{s.desc}</p>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                    {s.features.map(f => (
                      <div key={f} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <CheckCircle size={16} color={C.success} />
                        <span style={{ fontSize: 14, color: C.text }}>{f}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Why Choose Us */}
      <section style={{ padding: '80px 0', background: 'white' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 24px' }}>
          <div style={{ textAlign: 'center', marginBottom: 56 }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: C.primaryLight, color: C.primaryDark, borderRadius: 999, padding: '6px 16px', fontSize: 13, fontWeight: 700, marginBottom: 16 }}>
              <Sparkles size={16} /> Why Choose MediMitra
            </div>
            <h2 style={{ fontSize: 32, fontWeight: 800, color: C.text }}>Healthcare Reimagined</h2>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 24 }}>
            {[
              { icon: Shield, title: 'HIPAA Compliant', desc: 'Enterprise-grade security for your data' },
              { icon: Activity, title: '97% Accuracy', desc: 'AI trained on extensive medical datasets' },
              { icon: Clock, title: '24/7 Available', desc: 'Access screening services anytime' },
              { icon: Users, title: 'Expert Network', desc: '50+ healthcare professionals' },
            ].map(w => (
              <div key={w.title} style={{ textAlign: 'center', padding: 24 }}>
                <div style={{ width: 56, height: 56, background: C.primaryLight, borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
                  <w.icon size={28} color={C.primary} />
                </div>
                <h3 style={{ fontWeight: 700, color: C.text, marginBottom: 8 }}>{w.title}</h3>
                <p style={{ fontSize: 14, color: C.textSec }}>{w.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={{ padding: '64px 0', background: `linear-gradient(135deg, ${C.primaryDark}, ${C.primary})` }}>
        <div style={{ maxWidth: 800, margin: '0 auto', padding: '0 24px', textAlign: 'center' }}>
          <h2 style={{ fontSize: 32, fontWeight: 800, color: 'white', marginBottom: 16 }}>Experience AI-Powered Healthcare</h2>
          <p style={{ color: 'rgba(255,255,255,0.7)', marginBottom: 32 }}>Start your free health screening today.</p>
          <Link to="/ai-diagnosis" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: 'white', color: C.primaryDark, padding: '16px 32px', borderRadius: 14, fontWeight: 700, fontSize: 15, boxShadow: '0 8px 30px rgba(0,0,0,0.15)' }}>
            Start AI Diagnosis <ArrowRight size={18} />
          </Link>
        </div>
      </section>
    </div>
  );
}
