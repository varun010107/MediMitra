import { createContext, useContext, useState } from 'react';

const PatientContext = createContext();

export function PatientProvider({ children }) {
  const [patientInfo, setPatientInfo] = useState({
    name: '', age: '', gender: '', contact: '', medical_history: '',
  });
  const [selectedSymptoms, setSelectedSymptoms] = useState([]);
  const [symptomDescription, setSymptomDescription] = useState('');
  const [labReportText, setLabReportText] = useState('');
  const [questionnaire, setQuestionnaire] = useState([]);
  const [questionnaireAnswers, setQuestionnaireAnswers] = useState({});
  const [results, setResults] = useState(null);

  const reset = () => {
    setPatientInfo({ name: '', age: '', gender: '', contact: '', medical_history: '' });
    setSelectedSymptoms([]);
    setSymptomDescription('');
    setLabReportText('');
    setQuestionnaire([]);
    setQuestionnaireAnswers({});
    setResults(null);
  };

  return (
    <PatientContext.Provider value={{
      patientInfo, setPatientInfo,
      selectedSymptoms, setSelectedSymptoms,
      symptomDescription, setSymptomDescription,
      labReportText, setLabReportText,
      questionnaire, setQuestionnaire,
      questionnaireAnswers, setQuestionnaireAnswers,
      results, setResults,
      reset,
    }}>
      {children}
    </PatientContext.Provider>
  );
}

export const usePatient = () => useContext(PatientContext);
