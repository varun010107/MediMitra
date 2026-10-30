import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import doctorConsultationImage from '../assets/doctor-consultation.png';
import medicalCollaborationImage from '../assets/medical-collaboration.png';
import {
  Heart, Shield, Brain, Stethoscope, FileText, Users,
  ArrowRight, Activity, Clock, CheckCircle, Star, ChevronRight,
  Microscope, Pill, HeartPulse, UserCheck, Sparkles, Phone,
} from 'lucide-react';

const C = {
  primary: '#0A6E8A',
  primaryDark: '#064E63',
  primaryLight: '#E8F4F8',
  accent: '#2ECC71',
  accentDark: '#27AE60',
  teal: '#0E7C7B',
  tealLight: '#E6F7F6',
  text: '#1A202C',
  textSec: '#4A5568',
  textMuted: '#A0AEC0',
  bg: '#F0F5F7',
  border: '#E2E8F0',
  critical: '#E53E3E',
  amber: '#D69E2E',
  success: '#38A169',
};

const fadeUp = { hidden: { opacity: 0, y: 30 }, visible: { opacity: 1, y: 0 } };

export default function Home() {
  return (
    <div style={{ paddingTop: 72 }}>
      {/* ─── HERO ─── */}
      <section style={{
        position: 'relative', overflow: 'hidden',
        background: `linear-gradient(135deg, ${C.primaryDark} 0%, ${C.primary} 50%, ${C.teal} 100%)`,
        minHeight: '92vh', display: 'flex', alignItems: 'center',
      }}>
        <div style={{ position: 'absolute', inset: 0, opacity: 0.08 }}>
          <div style={{ position: 'absolute', top: 40, right: 80, width: 400, height: 400, background: 'white', borderRadius: '50%', filter: 'blur(80px)' }} />
          <div style={{ position: 'absolute', bottom: 40, left: 40, width: 300, height: 300, background: C.accent, borderRadius: '50%', filter: 'blur(80px)' }} />
        </div>
        <div style={{
          position: 'absolute', inset: 0,
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M30 5v20M20 15h20' stroke='%23fff' stroke-width='0.5' fill='none' opacity='0.05'/%3E%3C/svg%3E")`,
        }} />

        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '80px 24px', position: 'relative', zIndex: 10, width: '100%' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 48, alignItems: 'center' }}>
            <motion.div initial="hidden" animate="visible" variants={{ visible: { transition: { staggerChildren: 0.15 } } }}>
              <motion.div variants={fadeUp} style={{
                display: 'inline-flex', alignItems: 'center', gap: 8,
                background: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(12px)',
                border: '1px solid rgba(255,255,255,0.2)', borderRadius: 999,
                padding: '6px 16px', marginBottom: 24,
              }}>
                <Sparkles size={16} color={C.accent} />
                <span style={{ fontSize: 14, color: 'rgba(255,255,255,0.9)', fontWeight: 500 }}>Trusted by 135K+ patients</span>
              </motion.div>

              <motion.h1 variants={fadeUp} style={{
                fontSize: 56, fontWeight: 800, color: 'white', lineHeight: 1.1, letterSpacing: -2,
              }}>
                Your Trusted<br />Partner in<br />
                <span style={{ color: C.accent }}>Modern Healthcare</span>
              </motion.h1>

              <motion.p variants={fadeUp} style={{ fontSize: 17, color: 'rgba(255,255,255,0.7)', marginTop: 24, maxWidth: 480, lineHeight: 1.7 }}>
                Understand your symptoms with personalized AI questions, clear explanations, and a report to discuss with a healthcare professional.
              </motion.p>

              <motion.div variants={fadeUp} style={{ display: 'flex', gap: 16, marginTop: 32, flexWrap: 'wrap' }}>
                <Link to="/ai-diagnosis" style={{
                  display: 'inline-flex', alignItems: 'center', gap: 8,
                  background: 'white', color: C.primaryDark,
                  padding: '14px 28px', borderRadius: 14, fontWeight: 700, fontSize: 14,
                  boxShadow: '0 8px 30px rgba(0,0,0,0.15)',
                  transition: 'all 0.2s',
                }}>
                  Start AI Diagnosis <ArrowRight size={16} />
                </Link>
                <Link to="/services" style={{
                  display: 'inline-flex', alignItems: 'center', gap: 8,
                  background: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(12px)',
                  border: '1px solid rgba(255,255,255,0.2)', color: 'white',
                  padding: '14px 28px', borderRadius: 14, fontWeight: 600, fontSize: 14,
                }}>
                  Explore Services
                </Link>
              </motion.div>

              <motion.div variants={fadeUp} style={{ display: 'flex', gap: 32, marginTop: 48 }}>
                {[
                  { icon: UserCheck, val: '50+', lbl: 'Specialists' },
                  { icon: Activity, val: 'AI', lbl: 'Explained screening' },
                  { icon: Clock, val: '24/7', lbl: 'Support' },
                ].map(s => (
                  <div key={s.lbl} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{ width: 44, height: 44, background: 'rgba(255,255,255,0.1)', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <s.icon size={20} color="rgba(255,255,255,0.8)" />
                    </div>
                    <div>
                      <div style={{ fontSize: 22, fontWeight: 800, color: 'white' }}>{s.val}</div>
                      <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.5)' }}>{s.lbl}</div>
                    </div>
                  </div>
                ))}
              </motion.div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8, delay: 0.3 }}
              style={{ position: 'relative' }}
              className="hidden lg:block"
            >
              <div style={{ position: 'relative' }}>
                <div style={{ width: '100%', height: 520, borderRadius: 24, overflow: 'hidden', boxShadow: '0 25px 50px rgba(0,0,0,0.25)' }}>
                  <img
                    src={doctorConsultationImage}
                    alt="Doctor with patient"
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                  <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to top, rgba(6,78,99,0.4), transparent)' }} />
                </div>

                <div style={{
                  position: 'absolute', bottom: -24, left: -24,
                  background: 'white', borderRadius: 18, padding: 20,
                  boxShadow: '0 8px 30px rgba(0,0,0,0.1)', border: '1px solid #f0f0f0',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{ width: 48, height: 48, background: 'rgba(46,204,113,0.1)', borderRadius: 14, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <HeartPulse size={24} color={C.accentDark} />
                    </div>
                    <div>
                      <div style={{ fontSize: 28, fontWeight: 800, color: C.primaryDark }}>AI</div>
                      <div style={{ fontSize: 12, color: C.textMuted }}>Explained Screening</div>
                    </div>
                  </div>
                </div>

                <div style={{
                  position: 'absolute', top: -16, right: -16,
                  background: 'white', borderRadius: 16, padding: '12px 16px',
                  boxShadow: '0 8px 30px rgba(0,0,0,0.1)', border: '1px solid #f0f0f0',
                  display: 'flex', alignItems: 'center', gap: 8,
                }}>
                  <CheckCircle size={18} color={C.success} />
                  <span style={{ fontSize: 13, fontWeight: 700, color: C.text }}>AI Verified</span>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ─── STATS BAR ─── */}
      <section style={{ background: 'white', borderBottom: `1px solid ${C.border}` }}>
        <div style={{ maxWidth: 1024, margin: '0 auto', padding: '48px 24px', display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 32 }}>
          {[
            { icon: Users, value: '135K+', label: 'Patients Served' },
            { icon: Stethoscope, value: '50+', label: 'Healthcare Professionals' },
            { icon: Activity, value: 'AI', label: 'Explained screening' },
            { icon: Shield, value: 'Clear', label: 'Uncertainty & limitations' },
          ].map(s => (
            <div key={s.label} style={{ textAlign: 'center' }}>
              <s.icon size={24} color={C.primary} style={{ margin: '0 auto 8px' }} />
              <div style={{ fontSize: 32, fontWeight: 800, color: C.primaryDark }}>{s.value}</div>
              <div style={{ fontSize: 13, color: C.textMuted, marginTop: 4 }}>{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ─── ABOUT SECTION ─── */}
      <section style={{ padding: '80px 0', background: C.bg }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 24px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 64, alignItems: 'center' }}>
            <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={{ visible: { transition: { staggerChildren: 0.1 } } }}>
              <motion.div variants={fadeUp} style={{
                display: 'inline-flex', alignItems: 'center', gap: 8,
                background: C.primaryLight, color: C.primaryDark, borderRadius: 999,
                padding: '6px 16px', fontSize: 13, fontWeight: 700, marginBottom: 16,
              }}>
                <Heart size={16} /> About MediMitra
              </motion.div>
              <motion.h2 variants={fadeUp} style={{ fontSize: 36, fontWeight: 800, color: C.text, lineHeight: 1.2 }}>
                Connecting Doctors & Patients for <span style={{ color: C.primary }}>Holistic Healing</span>
              </motion.h2>
              <motion.p variants={fadeUp} style={{ color: C.textSec, marginTop: 20, lineHeight: 1.7 }}>
                MediMitra Clinic connects doctors and patients effortlessly, providing smarter, safer, and compassionate healthcare from diagnosis to full recovery. Our AI screening explains possible causes and uncertainty to support a conversation with a healthcare professional.
              </motion.p>

              <motion.div variants={fadeUp} style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginTop: 32 }}>
                {[
                  { icon: Heart, label: 'Smart Care', color: '#FEE2E2', iconColor: '#EF4444' },
                  { icon: Shield, label: 'Connected Care', color: '#DBEAFE', iconColor: '#3B82F6' },
                  { icon: Brain, label: 'Data Privacy', color: '#EDE9FE', iconColor: '#8B5CF6' },
                ].map(f => (
                  <div key={f.label} style={{ background: 'white', borderRadius: 16, padding: 16, border: `1px solid ${C.border}`, textAlign: 'center' }}>
                    <div style={{ width: 40, height: 40, background: f.color, borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 8px' }}>
                      <f.icon size={20} color={f.iconColor} />
                    </div>
                    <div style={{ fontSize: 13, fontWeight: 700, color: C.text }}>{f.label}</div>
                  </div>
                ))}
              </motion.div>
            </motion.div>

            <div style={{ position: 'relative' }}>
              <img
                src={medicalCollaborationImage}
                alt="Medical team"
                style={{ borderRadius: 24, boxShadow: '0 20px 40px rgba(0,0,0,0.1)', width: '100%', height: 400, objectFit: 'cover' }}
              />
              <div style={{
                position: 'absolute', bottom: -24, right: -24,
                background: 'white', borderRadius: 18, padding: 20,
                boxShadow: '0 8px 30px rgba(0,0,0,0.1)', border: `1px solid ${C.border}`,
              }}>
                <div style={{ fontSize: 32, fontWeight: 800, color: C.primaryDark }}>50+</div>
                <div style={{ fontSize: 12, color: C.textMuted }}>Healthcare Professionals<br/>Supporting Lives Worldwide</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── SERVICES ─── */}
      <section style={{ padding: '80px 0', background: 'white' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 24px' }}>
          <div style={{ textAlign: 'center', marginBottom: 56 }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              background: C.primaryLight, color: C.primaryDark, borderRadius: 999,
              padding: '6px 16px', fontSize: 13, fontWeight: 700, marginBottom: 16,
            }}>
              <Stethoscope size={16} /> Our Services
            </div>
            <h2 style={{ fontSize: 36, fontWeight: 800, color: C.text }}>The MediMitra Total Care&trade; Model</h2>
            <p style={{ color: C.textSec, marginTop: 12, maxWidth: 600, margin: '12px auto 0' }}>
              Providing patient-centered care through expert guidance, innovative solutions, and personalized support every step of the way.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 24 }}>
            {[
              { icon: Brain, title: 'AI Health Screening', desc: 'Personalized questions based on your symptoms and medical history, with clear uncertainty when evidence is limited.', color: '#DBEAFE', iconColor: '#2563EB' },
              { icon: Microscope, title: 'Lab Report Analysis', desc: 'Multimodal AI reads and interprets your lab reports, identifying out-of-range values and clinical implications.', color: '#EDE9FE', iconColor: '#7C3AED' },
              { icon: Stethoscope, title: 'Doctor Consultation', desc: 'Get matched with the right specialist based on your symptoms and AI screening results.', color: C.tealLight, iconColor: C.teal },
              { icon: FileText, title: 'Clinical Reports', desc: "Downloadable PDF reports explaining possible causes, supporting facts, and what remains uncertain.", color: '#FFF7ED', iconColor: '#EA580C' },
              { icon: Pill, title: 'Precautionary Guidance', desc: 'Evidence-based precautionary measures and lifestyle recommendations tailored to your condition.', color: '#DCFCE7', iconColor: '#16A34A' },
              { icon: Phone, title: 'Emergency Triage', desc: 'Instant identification of critical conditions with emergency routing and SOS capabilities.', color: '#FEE2E2', iconColor: '#DC2626' },
            ].map(s => (
              <motion.div
                key={s.title}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                variants={fadeUp}
                style={{
                  background: 'white', borderRadius: 20, padding: 28,
                  border: `1px solid ${C.border}`,
                  transition: 'all 0.3s',
                  cursor: 'pointer',
                }}
                whileHover={{ y: -4, boxShadow: '0 12px 40px rgba(10,110,138,0.08)' }}
              >
                <div style={{ width: 56, height: 56, background: s.color, borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 20 }}>
                  <s.icon size={28} color={s.iconColor} />
                </div>
                <h3 style={{ fontSize: 18, fontWeight: 700, color: C.text, marginBottom: 8 }}>{s.title}</h3>
                <p style={{ fontSize: 14, color: C.textSec, lineHeight: 1.6 }}>{s.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── HOW IT WORKS ─── */}
      <section style={{ padding: '80px 0', background: C.bg }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 24px' }}>
          <div style={{ textAlign: 'center', marginBottom: 56 }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              background: C.primaryLight, color: C.primaryDark, borderRadius: 999,
              padding: '6px 16px', fontSize: 13, fontWeight: 700, marginBottom: 16,
            }}>
              <Activity size={16} /> How It Works
            </div>
            <h2 style={{ fontSize: 36, fontWeight: 800, color: C.text }}>Your Journey to Better Health</h2>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 24 }}>
            {[
              { step: '01', title: 'Patient Details', desc: 'Enter your basic information and medical history', icon: Users, gradient: 'linear-gradient(135deg, #3B82F6, #2563EB)' },
              { step: '02', title: 'Symptom Assessment', desc: 'Select symptoms and describe your condition', icon: Stethoscope, gradient: 'linear-gradient(135deg, #8B5CF6, #7C3AED)' },
              { step: '03', title: 'AI Questionnaire', desc: 'Answer questions tailored to your symptoms and history', icon: Brain, gradient: `linear-gradient(135deg, ${C.teal}, ${C.primary})` },
              { step: '04', title: 'Get Results', desc: 'Review possibilities, uncertainty, and next steps', icon: FileText, gradient: `linear-gradient(135deg, ${C.accentDark}, ${C.accent})` },
            ].map((s, i) => (
              <motion.div
                key={s.step}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15 }}
                style={{ position: 'relative' }}
              >
                <div style={{
                  background: 'white', borderRadius: 20, padding: 28,
                  border: `1px solid ${C.border}`, textAlign: 'center',
                  height: '100%', transition: 'box-shadow 0.3s',
                }}>
                  <div style={{
                    width: 56, height: 56, background: s.gradient, borderRadius: 16,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    margin: '0 auto 20px', boxShadow: '0 8px 20px rgba(0,0,0,0.15)',
                  }}>
                    <s.icon size={28} color="white" />
                  </div>
                  <div style={{ fontSize: 11, fontWeight: 800, color: C.textMuted, letterSpacing: 3, marginBottom: 8 }}>STEP {s.step}</div>
                  <h3 style={{ fontSize: 18, fontWeight: 700, color: C.text, marginBottom: 8 }}>{s.title}</h3>
                  <p style={{ fontSize: 13, color: C.textSec }}>{s.desc}</p>
                </div>
                {i < 3 && (
                  <div className="hidden md:block" style={{ position: 'absolute', top: '50%', right: -12, transform: 'translateY(-50%)', zIndex: 10 }}>
                    <ChevronRight size={24} color={C.textMuted} />
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── TESTIMONIALS ─── */}
      <section style={{ padding: '80px 0', background: 'white' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 24px' }}>
          <div style={{ textAlign: 'center', marginBottom: 56 }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              background: C.primaryLight, color: C.primaryDark, borderRadius: 999,
              padding: '6px 16px', fontSize: 13, fontWeight: 700, marginBottom: 16,
            }}>
              <Star size={16} /> Testimonials
            </div>
            <h2 style={{ fontSize: 36, fontWeight: 800, color: C.text }}>Real Stories, Real Healing</h2>
            <p style={{ color: C.textSec, marginTop: 12, maxWidth: 520, margin: '12px auto 0' }}>
              Providing patient-centered care through expert guidance, innovative solutions, and personalized support every step of the way.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 24 }}>
            {[
              { name: 'Priya Sharma', role: 'Patient', text: "MediMitra's AI screening identified my thyroid issue early. The questionnaire was thorough and the doctor recommendation was spot on. Highly recommend!" },
              { name: 'Dr. Rajesh Kumar', role: 'Physician', text: 'As a doctor, the clinician portal saves me significant time. The AI pre-screening gives me a solid foundation before the actual consultation.' },
              { name: 'Anita Desai', role: 'Patient', text: 'The lab report scanner is incredible — it extracted and flagged my abnormal values instantly. The entire process felt seamless and supportive.' },
            ].map(t => (
              <div key={t.name} style={{
                background: 'white', borderRadius: 20, padding: 28,
                border: `1px solid ${C.border}`, transition: 'box-shadow 0.3s',
              }}>
                <div style={{ display: 'flex', gap: 4, marginBottom: 16 }}>
                  {[1,2,3,4,5].map(i => <Star key={i} size={16} color={C.amber} fill={C.amber} />)}
                </div>
                <p style={{ color: C.textSec, fontSize: 14, lineHeight: 1.7, marginBottom: 20 }}>"{t.text}"</p>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{
                    width: 40, height: 40, borderRadius: '50%',
                    background: `linear-gradient(135deg, ${C.primary}, ${C.teal})`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: 'white', fontWeight: 700, fontSize: 14,
                  }}>
                    {t.name.charAt(0)}
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 14, color: C.text }}>{t.name}</div>
                    <div style={{ fontSize: 12, color: C.textMuted }}>{t.role}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA ─── */}
      <section style={{
        padding: '80px 0', position: 'relative', overflow: 'hidden',
        background: `linear-gradient(135deg, ${C.primaryDark} 0%, ${C.primary} 50%, ${C.teal} 100%)`,
      }}>
        <div style={{ position: 'absolute', inset: 0, opacity: 0.1 }}>
          <div style={{ position: 'absolute', top: 20, left: 20, width: 250, height: 250, background: 'white', borderRadius: '50%', filter: 'blur(80px)' }} />
          <div style={{ position: 'absolute', bottom: 20, right: 20, width: 200, height: 200, background: C.accent, borderRadius: '50%', filter: 'blur(80px)' }} />
        </div>
        <div style={{ maxWidth: 800, margin: '0 auto', padding: '0 24px', textAlign: 'center', position: 'relative', zIndex: 10 }}>
          <h2 style={{ fontSize: 36, fontWeight: 800, color: 'white', marginBottom: 16 }}>
            Ready for Smarter Healthcare?
          </h2>
          <p style={{ fontSize: 17, color: 'rgba(255,255,255,0.7)', marginBottom: 32, maxWidth: 600, margin: '0 auto 32px' }}>
            Start your AI-powered health screening today. Get accurate insights, expert recommendations, and take control of your well-being.
          </p>
          <Link to="/ai-diagnosis" style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            background: 'white', color: C.primaryDark,
            padding: '16px 32px', borderRadius: 14, fontWeight: 700, fontSize: 15,
            boxShadow: '0 8px 30px rgba(0,0,0,0.15)',
          }}>
            Begin Your Health Assessment <ArrowRight size={18} />
          </Link>
          <Link to="/skin" style={{
            display: 'inline-flex', alignItems: 'center', gap: 8, marginLeft: 12,
            background: 'rgba(255,255,255,0.12)', color: 'white', border: '1px solid rgba(255,255,255,0.35)',
            padding: '16px 32px', borderRadius: 14, fontWeight: 700, fontSize: 15,
          }}>
            Try Skin Lesion Analysis <Microscope size={18} />
          </Link>
        </div>
      </section>
    </div>
  );
}
