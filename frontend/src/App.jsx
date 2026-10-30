import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { PatientProvider } from './context/PatientContext';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Home from './pages/Home';
import About from './pages/About';
import Services from './pages/Services';
import Contact from './pages/Contact';
import AIDiagnosis from './pages/AIDiagnosis';
import SkinApp from './modules/skin/SkinApp';

function App() {
  return (
    <BrowserRouter>
      <PatientProvider>
        <div className="min-h-screen flex flex-col">
          <Navbar />
          <main className="flex-1">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/about" element={<About />} />
              <Route path="/services" element={<Services />} />
              <Route path="/contact" element={<Contact />} />
              <Route path="/ai-diagnosis" element={<AIDiagnosis />} />
              <Route path="/skin/*" element={<SkinApp />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </PatientProvider>
    </BrowserRouter>
  );
}

export default App;
