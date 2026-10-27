import { Link } from 'react-router-dom';
import { Heart, Mail, Phone, MapPin } from 'lucide-react';

const C = { primaryDark: '#064E63', textMuted: '#A0AEC0' };

export default function Footer() {
  return (
    <footer style={{ background: C.primaryDark, color: 'white' }}>
      <div style={{ maxWidth: 1280, margin: '0 auto', padding: '64px 24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 200px), 1fr))', gap: 40 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
              <div style={{ width: 40, height: 40, background: 'rgba(255,255,255,0.1)', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Heart size={20} color="white" fill="white" />
              </div>
              <span style={{ fontSize: 20, fontWeight: 800 }}>MediMitra</span>
            </div>
            <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: 14, lineHeight: 1.7 }}>
              AI-powered clinical intelligence platform providing smarter, safer, and more compassionate healthcare from diagnosis to recovery.
            </p>
          </div>

          <div>
            <h4 style={{ fontWeight: 700, marginBottom: 16, color: 'rgba(255,255,255,0.9)' }}>Quick Links</h4>
            {[['/', 'Home'], ['/about', 'About Us'], ['/services', 'Services'], ['/ai-diagnosis', 'AI Screening'], ['/contact', 'Contact']].map(([to, label]) => (
              <Link key={to} to={to} style={{ display: 'block', fontSize: 14, color: 'rgba(255,255,255,0.45)', marginBottom: 10, transition: 'color 0.2s' }}>{label}</Link>
            ))}
          </div>

          <div>
            <h4 style={{ fontWeight: 700, marginBottom: 16, color: 'rgba(255,255,255,0.9)' }}>Our Services</h4>
            {['AI Health Screening', 'Lab Report Analysis', 'Symptom Assessment', 'Doctor Recommendations', 'Emergency Triage'].map(s => (
              <p key={s} style={{ fontSize: 14, color: 'rgba(255,255,255,0.45)', marginBottom: 10 }}>{s}</p>
            ))}
          </div>

          <div>
            <h4 style={{ fontWeight: 700, marginBottom: 16, color: 'rgba(255,255,255,0.9)' }}>Contact Us</h4>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 12 }}>
              <Phone size={16} style={{ marginTop: 2, flexShrink: 0, opacity: 0.5 }} />
              <div style={{ fontSize: 14, color: 'rgba(255,255,255,0.45)' }}>
                <p>Emergency: 108 / 112</p>
                <p>Helpline: +91-1800-XXX-XXXX</p>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 12 }}>
              <Mail size={16} style={{ marginTop: 2, flexShrink: 0, opacity: 0.5 }} />
              <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.45)' }}>support@medimitra.health</p>
            </div>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
              <MapPin size={16} style={{ marginTop: 2, flexShrink: 0, opacity: 0.5 }} />
              <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.45)' }}>Health Innovation Hub, India</p>
            </div>
          </div>
        </div>

        <div style={{ borderTop: '1px solid rgba(255,255,255,0.1)', marginTop: 48, paddingTop: 32, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
          <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.35)' }}>&copy; {new Date().getFullYear()} MediMitra. All rights reserved.</p>
          <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.25)' }}>AI-assisted screening tool. Not a substitute for professional medical advice.</p>
        </div>
      </div>
    </footer>
  );
}
