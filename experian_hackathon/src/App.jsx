import { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import reactLogo from './assets/react.svg';
import viteLogo from '/vite.svg';
import './App.css';

function App() {
  const [count, setCount] = useState(0);
  const [resumeData, setResumeData] = useState(null);

  const onDrop = async (acceptedFiles) => {
    const file = acceptedFiles[0];
    const fileType = file.type;

    if (fileType === 'application/pdf' || fileType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' || fileType.startsWith('image/')) {
      const formData = new FormData();
      formData.append('file', file);

      try {
        console.log('Uploading file...');
        const response = await axios.post(
          `${import.meta.env.VITE_FORM_RECOGNIZER_ENDPOINT}/formrecognizer/v2.1-preview.3/layout/analyze`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
              'Ocp-Apim-Subscription-Key': import.meta.env.VITE_FORM_RECOGNIZER_API_KEY,
            },
          }
        );

        console.log('File uploaded, waiting for analysis...');
        const operationLocation = response.headers['operation-location'];
        const result = await getAnalysisResult(operationLocation);
        extractKeyInformation(result);
      } catch (error) {
        console.error('Error uploading file:', error);
      }
    } else {
      console.error('Unsupported file type');
    }
  };

  const getAnalysisResult = async (operationLocation) => {
    let result = null;
    while (!result) {
      const response = await axios.get(operationLocation, {
        headers: {
          'Ocp-Apim-Subscription-Key': import.meta.env.VITE_FORM_RECOGNIZER_API_KEY,
        },
      });

      if (response.data.status === 'succeeded') {
        result = response.data;
      } else if (response.data.status === 'failed') {
        throw new Error('Analysis failed');
      } else {
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }
    }
    return result;
  };

  const extractKeyInformation = (result) => {
    console.log('Extracted data:', result);
    setResumeData(JSON.stringify(result, null, 2));
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