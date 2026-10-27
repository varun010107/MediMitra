import { motion } from 'framer-motion';
import medicalTeamImage from '../assets/medical-team.png';
import { Heart, Shield, Users, Award, Target, Eye, CheckCircle } from 'lucide-react';

const C = {
  primary: '#0A6E8A', primaryDark: '#064E63', primaryLight: '#E8F4F8',
  accent: '#2ECC71', accentDark: '#27AE60', teal: '#0E7C7B', tealLight: '#E6F7F6',
  text: '#1A202C', textSec: '#4A5568', textMuted: '#A0AEC0',
  bg: '#F0F5F7', border: '#E2E8F0', success: '#38A169',
};

const fadeUp = { hidden: { opacity: 0, y: 30 }, visible: { opacity: 1, y: 0 } };

export default function About() {
  return (
    <div style={{ paddingTop: 72 }}>
      {/* Hero */}
      <section style={{ position: 'relative', background: `linear-gradient(135deg, ${C.primaryDark}, ${C.primary}, ${C.teal})`, padding: '96px 0', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', inset: 0, opacity: 0.1 }}>
          <div style={{ position: 'absolute', top: 40, right: 80, width: 400, height: 400, background: 'white', borderRadius: '50%', filter: 'blur(80px)' }} />
        </div>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 24px', position: 'relative', zIndex: 10, textAlign: 'center' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 999, padding: '6px 16px', fontSize: 13, color: 'rgba(255,255,255,0.9)', fontWeight: 600, marginBottom: 24 }}>
            <Heart size={16} /> About MediMitra
          </div>
          <h1 style={{ fontSize: 48, fontWeight: 800, color: 'white', marginBottom: 16 }}>Transforming Healthcare<br/>Through Innovation</h1>
          <p style={{ fontSize: 17, color: 'rgba(255,255,255,0.7)', maxWidth: 600, margin: '0 auto' }}>
            We're committed to delivering the highest standard of medical care with sensitivity, powered by artificial intelligence and human compassion.
          </p>
        </div>
      </section>

      {/* Mission & Vision */}
      <section style={{ padding: '80px 0', background: 'white' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 24px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 48 }}>
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp}
            style={{ background: C.primaryLight, borderRadius: 24, padding: 40 }}>
            <div style={{ width: 56, height: 56, background: 'rgba(10,110,138,0.1)', borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 24 }}>
              <Target size={28} color={C.primary} />
            </div>
            <h2 style={{ fontSize: 26, fontWeight: 800, color: C.text, marginBottom: 16 }}>Our Mission</h2>
            <p style={{ color: C.textSec, lineHeight: 1.7 }}>To democratize healthcare access by combining the power of AI with medical expertise, ensuring every patient receives accurate, timely, and compassionate care regardless of their location or circumstances.</p>
          </motion.div>

          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp}
            style={{ background: C.bg, borderRadius: 24, padding: 40 }}>
            <div style={{ width: 56, height: 56, background: 'rgba(46,204,113,0.1)', borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 24 }}>
              <Eye size={28} color={C.accentDark} />
            </div>
            <h2 style={{ fontSize: 26, fontWeight: 800, color: C.text, marginBottom: 16 }}>Our Vision</h2>
            <p style={{ color: C.textSec, lineHeight: 1.7 }}>A world where AI-assisted healthcare bridges the gap between patients and doctors, making preliminary diagnosis accessible, reliable, and empowering for everyone.</p>
          </motion.div>
        </div>
      </section>

      {/* Values */}
      <section style={{ padding: '80px 0', background: C.bg }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 24px' }}>
          <div style={{ textAlign: 'center', marginBottom: 56 }}>
            <h2 style={{ fontSize: 32, fontWeight: 800, color: C.text }}>Our Core Values</h2>
            <p style={{ color: C.textSec, marginTop: 12 }}>The principles that guide everything we do</p>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 24 }}>
            {[
              { icon: Heart, title: 'Compassion', desc: 'Treating every patient with empathy and care, ensuring the human element is never lost in technology.', color: '#FEE2E2', iconColor: '#EF4444' },
              { icon: Shield, title: 'Trust & Privacy', desc: 'Being clear about how information is used and the limitations of this educational prototype.', color: '#DBEAFE', iconColor: '#3B82F6' },
              { icon: Award, title: 'Excellence', desc: 'Improving the clarity of AI questions, explanations, and uncertainty for professional review.', color: '#FEF3C7', iconColor: '#D97706' },
              { icon: Users, title: 'Collaboration', desc: 'Bridging AI intelligence with physician expertise for comprehensive patient care.', color: '#DCFCE7', iconColor: '#16A34A' },
              { icon: CheckCircle, title: 'Transparency', desc: 'Clear communication about AI limitations and always recommending professional verification.', color: '#EDE9FE', iconColor: '#7C3AED' },
              { icon: Target, title: 'Accessibility', desc: 'Making quality healthcare screening available to everyone, everywhere, at any time.', color: C.tealLight, iconColor: C.teal },
            ].map(v => (
              <motion.div key={v.title} initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp}
                style={{ background: 'white', borderRadius: 20, padding: 28, border: `1px solid ${C.border}`, transition: 'box-shadow 0.3s' }}>
                <div style={{ width: 48, height: 48, background: v.color, borderRadius: 14, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
                  <v.icon size={24} color={v.iconColor} />
                </div>
                <h3 style={{ fontSize: 18, fontWeight: 700, color: C.text, marginBottom: 8 }}>{v.title}</h3>
                <p style={{ fontSize: 14, color: C.textSec, lineHeight: 1.6 }}>{v.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Team */}
      <section style={{ padding: '80px 0', background: 'white' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 24px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 48, alignItems: 'center' }}>
          <div>
            <img src={medicalTeamImage} alt="Medical team" style={{ borderRadius: 24, boxShadow: '0 20px 40px rgba(0,0,0,0.1)', width: '100%', height: 400, objectFit: 'cover' }} />
          </div>
          <div>
            <h2 style={{ fontSize: 32, fontWeight: 800, color: C.text, marginBottom: 24 }}>A Team Dedicated to Your Well-being</h2>
            <p style={{ color: C.textSec, lineHeight: 1.7, marginBottom: 24 }}>Our platform unites doctors, specialists, and wellness experts in one place. From diagnostics to recovery, we ensure holistic healing and long-term wellness.</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {[
                'AI screening with personalized questions and clear uncertainty',
                'Expert physician review and sign-off on every case',
                'Comprehensive lab report analysis with multimodal OCR',
                'Emergency triage and instant SOS routing',
              ].map(item => (
                <div key={item} style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                  <CheckCircle size={20} color={C.success} style={{ marginTop: 2, flexShrink: 0 }} />
                  <span style={{ fontSize: 14, color: C.textSec }}>{item}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
