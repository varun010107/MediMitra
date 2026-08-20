import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Heart, Phone } from 'lucide-react';

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();

  const links = [
    { to: '/', label: 'Home' },
    { to: '/about', label: 'About' },
    { to: '/services', label: 'Services' },
    { to: '/ai-diagnosis', label: 'AI Diagnosis' },
    { to: '/contact', label: 'Contact' },
  ];

  return (
    <nav style={{ position: 'fixed', top: 0, left: 0, right: 0, zIndex: 50, background: 'rgba(255,255,255,0.97)', backdropFilter: 'blur(12px)', borderBottom: '1px solid #E2E8F0', boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}>
      <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 72 }}>
          {/* Logo */}
          <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 42, height: 42, background: 'linear-gradient(135deg, #0A6E8A, #0E7C7B)', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Heart size={22} color="white" fill="white" />
            </div>
            <div>
              <div style={{ fontSize: 20, fontWeight: 800, color: '#064E63', letterSpacing: -0.5 }}>MediMitra</div>
              <div style={{ fontSize: 9, color: '#A0AEC0', letterSpacing: 2, textTransform: 'uppercase', marginTop: -2 }}>Clinical Intelligence</div>
            </div>
          </Link>

          {/* Desktop Nav Links */}
          <div className="hidden md:flex" style={{ alignItems: 'center', gap: 4 }}>
            {links.map(l => (
              <Link
                key={l.to}
                to={l.to}
                style={{
                  padding: '8px 18px',
                  borderRadius: 10,
                  fontSize: 14,
                  fontWeight: 600,
                  transition: 'all 0.2s',
                  background: pathname === l.to ? '#E8F4F8' : 'transparent',
                  color: pathname === l.to ? '#064E63' : '#4A5568',
                }}
              >
                {l.label}
              </Link>
            ))}
          </div>

          {/* Right side */}
          <div className="hidden md:flex" style={{ alignItems: 'center', gap: 16 }}>
            <a href="tel:108" style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: '#E53E3E', fontWeight: 700 }}>
              <Phone size={15} />
              Emergency: 108
            </a>
            <Link
              to="/ai-diagnosis"
              style={{
                background: 'linear-gradient(135deg, #0A6E8A, #0E7C7B)',
                color: 'white',
                padding: '10px 22px',
                borderRadius: 12,
                fontSize: 13,
                fontWeight: 700,
                boxShadow: '0 4px 14px rgba(10,110,138,0.3)',
                transition: 'all 0.2s',
              }}
            >
              Book Consultation
            </Link>
          </div>

          {/* Mobile menu button */}
          <button onClick={() => setOpen(!open)} className="md:hidden" style={{ padding: 8, borderRadius: 8, background: 'none', border: 'none', cursor: 'pointer' }}>
            {open ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile dropdown */}
      {open && (
        <div className="md:hidden" style={{ background: 'white', borderTop: '1px solid #E2E8F0', padding: '12px 16px', boxShadow: '0 10px 30px rgba(0,0,0,0.1)' }}>
          {links.map(l => (
            <Link
              key={l.to}
              to={l.to}
              onClick={() => setOpen(false)}
              style={{
                display: 'block',
                padding: '12px 16px',
                borderRadius: 12,
                fontSize: 14,
                fontWeight: 600,
                background: pathname === l.to ? '#E8F4F8' : 'transparent',
                color: pathname === l.to ? '#064E63' : '#4A5568',
                marginBottom: 4,
              }}
            >
              {l.label}
            </Link>
          ))}
          <Link
            to="/ai-diagnosis"
            onClick={() => setOpen(false)}
            style={{
              display: 'block',
              textAlign: 'center',
              background: 'linear-gradient(135deg, #0A6E8A, #0E7C7B)',
              color: 'white',
              padding: '12px 20px',
              borderRadius: 12,
              fontSize: 14,
              fontWeight: 700,
              marginTop: 8,
            }}
          >
            Book Consultation
          </Link>
        </div>
      )}
    </nav>
  );
}
