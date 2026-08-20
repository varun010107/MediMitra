import { useState } from 'react';
import { motion } from 'framer-motion';
import { Mail, Phone, MapPin, Clock, Send, MessageSquare } from 'lucide-react';

const C = {
  primary: '#0A6E8A', primaryDark: '#064E63', primaryLight: '#E8F4F8',
  teal: '#0E7C7B', text: '#1A202C', textSec: '#4A5568', textMuted: '#A0AEC0',
  bg: '#F0F5F7', border: '#E2E8F0', success: '#38A169', successBg: '#F0FFF4',
};

const fadeUp = { hidden: { opacity: 0, y: 30 }, visible: { opacity: 1, y: 0 } };
const inputStyle = { width: '100%', padding: '12px 16px', borderRadius: 12, border: `1px solid ${C.border}`, background: C.bg, fontSize: 14, outline: 'none', fontFamily: 'inherit' };

export default function Contact() {
  const [form, setForm] = useState({ name: '', email: '', subject: '', message: '' });
  const [sent, setSent] = useState(false);

  const handleSubmit = (e) => { e.preventDefault(); setSent(true); setTimeout(() => setSent(false), 3000); };

  return (
    <div style={{ paddingTop: 72 }}>
      <section style={{ position: 'relative', background: `linear-gradient(135deg, ${C.primaryDark}, ${C.primary}, ${C.teal})`, padding: '96px 0', overflow: 'hidden' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 24px', textAlign: 'center', position: 'relative', zIndex: 10 }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 999, padding: '6px 16px', fontSize: 13, color: 'rgba(255,255,255,0.9)', fontWeight: 600, marginBottom: 24 }}>
            <MessageSquare size={16} /> Get In Touch
          </div>
          <h1 style={{ fontSize: 48, fontWeight: 800, color: 'white', marginBottom: 16 }}>Contact Us</h1>
          <p style={{ fontSize: 17, color: 'rgba(255,255,255,0.7)', maxWidth: 500, margin: '0 auto' }}>Have questions about our AI healthcare platform? We'd love to hear from you.</p>
        </div>
      </section>

      <section style={{ padding: '80px 0', background: C.bg }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 24px', display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 32 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            {[
              { icon: Phone, title: 'Phone', lines: ['Emergency: 108 / 112', 'Helpline: +91-1800-XXX-XXXX'] },
              { icon: Mail, title: 'Email', lines: ['support@medimitra.health', 'admin@medimitra.health'] },
              { icon: MapPin, title: 'Address', lines: ['Health Innovation Hub', 'Mumbai, Maharashtra, India'] },
              { icon: Clock, title: 'Working Hours', lines: ['AI Screening: 24/7', 'Support: Mon-Sat, 9AM-6PM'] },
            ].map(c => (
              <motion.div key={c.title} initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp}
                style={{ background: 'white', borderRadius: 20, padding: 24, border: `1px solid ${C.border}`, display: 'flex', alignItems: 'flex-start', gap: 16 }}>
                <div style={{ width: 48, height: 48, background: C.primaryLight, borderRadius: 14, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <c.icon size={24} color={C.primary} />
                </div>
                <div>
                  <h3 style={{ fontWeight: 700, color: C.text, marginBottom: 4 }}>{c.title}</h3>
                  {c.lines.map(l => <p key={l} style={{ fontSize: 14, color: C.textSec }}>{l}</p>)}
                </div>
              </motion.div>
            ))}
          </div>

          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp}>
            <div style={{ background: 'white', borderRadius: 24, padding: 40, border: `1px solid ${C.border}` }}>
              <h2 style={{ fontSize: 24, fontWeight: 800, color: C.text, marginBottom: 8 }}>Send us a Message</h2>
              <p style={{ color: C.textSec, fontSize: 14, marginBottom: 32 }}>Fill out the form and we'll get back to you within 24 hours.</p>

              {sent ? (
                <div style={{ background: C.successBg, borderRadius: 20, padding: 40, textAlign: 'center' }}>
                  <div style={{ width: 64, height: 64, background: 'rgba(56,161,105,0.1)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
                    <Send size={32} color={C.success} />
                  </div>
                  <h3 style={{ fontSize: 20, fontWeight: 700, color: C.success, marginBottom: 8 }}>Message Sent!</h3>
                  <p style={{ fontSize: 14, color: C.textSec }}>Thank you for contacting us.</p>
                </div>
              ) : (
                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                    <div>
                      <label style={{ display: 'block', fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 6 }}>Full Name</label>
                      <input type="text" required value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Your name" style={inputStyle} />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 6 }}>Email</label>
                      <input type="email" required value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} placeholder="you@example.com" style={inputStyle} />
                    </div>
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 6 }}>Subject</label>
                    <input type="text" required value={form.subject} onChange={e => setForm({ ...form, subject: e.target.value })} placeholder="How can we help?" style={inputStyle} />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 6 }}>Message</label>
                    <textarea required rows={5} value={form.message} onChange={e => setForm({ ...form, message: e.target.value })} placeholder="Your message..." style={{ ...inputStyle, resize: 'none' }} />
                  </div>
                  <button type="submit" style={{
                    width: '100%', background: `linear-gradient(135deg, ${C.primary}, ${C.teal})`, color: 'white',
                    padding: '14px 0', borderRadius: 12, fontWeight: 700, fontSize: 14, border: 'none', cursor: 'pointer',
                    boxShadow: '0 4px 14px rgba(10,110,138,0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                  }}>
                    <Send size={16} /> Send Message
                  </button>
                </form>
              )}
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
