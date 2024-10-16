import { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { getDocument } from 'pdfjs-dist/build/pdf';
import { Document } from 'docx';
import Tesseract from 'tesseract.js';
import reactLogo from './assets/react.svg';
import viteLogo from '/vite.svg';
import './App.css';

function App() {
  const [count, setCount] = useState(0);
  const [resumeData, setResumeData] = useState(null);

  const onDrop = async (acceptedFiles) => {
    const file = acceptedFiles[0];
    const fileType = file.type;

    if (fileType === 'application/pdf') {
      const fileReader = new FileReader();
      fileReader.onload = async function () {
        const typedArray = new Uint8Array(this.result);
        const pdf = await getDocument({ data: typedArray }).promise;
        let text = '';
        for (let i = 1; i <= pdf.numPages; i++) {
          const page = await pdf.getPage(i);
          const content = await page.getTextContent();
          text += content.items.map((item) => item.str).join(' ');
        }
        extractKeyInformation(text);
      };
      fileReader.readAsArrayBuffer(file);
    } else if (fileType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
      const data = await file.arrayBuffer();
      const doc = new Document(data);
      const text = await doc.getText();
      extractKeyInformation(text);
    } else if (fileType.startsWith('image/')) {
      const { data: { text } } = await Tesseract.recognize(file, 'eng');
      extractKeyInformation(text);
    } else {
      console.error('Unsupported file type');
    }
  };

  const extractKeyInformation = (text) => {
    // Your extraction logic here...
    setResumeData(text);
  };

  const { getRootProps, getInputProps } = useDropzone({ onDrop });

  return (
    <>
      <div>
        <a href="https://vitejs.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
        <p>
          Edit <code>src/App.jsx</code> and save to test HMR
        </p>
      </div>
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
      <div {...getRootProps()} className="dropzone">
        <input {...getInputProps()} />
        <p>Drag 'n' drop a resume here, or click to select one</p>
      </div>
      {resumeData && (
        <div className="resume-data">
          <h2>Extracted Resume Data</h2>
          <pre>{resumeData}</pre>
        </div>
      )}
    </>
  );
}

export default App;
