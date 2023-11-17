import React, { useState } from 'react';
import './App.css';

const fileToDataUrl = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (event) => {
      resolve(event.target.result);
    };
    reader.onerror = (error) => {
      reject(error);
    };
    reader.readAsDataURL(file);
  });
};


function App() {
  const [hash, setHash] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [storing, setStoring] = useState(false);
  const [retrieving, setRetrieving] = useState(false);
  const [response, setResponse] = useState(null);

  const handleStore = async () => {
    try {
      if (!selectedFile) {
        console.error('No file selected');
        return;
      }
      setStoring(true)
      const formData = new FormData();
      formData.append('file', selectedFile);
  
      const res = await fetch('http://localhost:8000/store/', {
        method: 'POST',
        body: formData,
      });
      setStoring(false)

      if (!res.ok) {
        console.error('Error response from server:', res);
        return;
      }
  
      const result = await res.json();
      console.log('Server response:', result);
      setResponse(result);
    } catch (error) {
      console.error('Error storing data:', error);
    }
  };
  

  const handleRetrieve = async () => {
    try {
      if (!hash) {
        console.error('No hash provided');
        return;
      }
      setRetrieving(true)
      const response = await fetch(`http://localhost:8000/retrieve/?hash=${hash}`);
      if (!response.ok) {
        console.error('Error response from server:', response);
        return;
      }
      setRetrieving(false)
      // Extract filename from Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition');
      const filenameMatch = contentDisposition && contentDisposition.match(/filename="(.+)"/);
      const filename = filenameMatch ? filenameMatch[1] : 'downloaded-file';

      // Convert the response to a blob
      const blob = await response.blob();

      // Create a download link and trigger the download
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('Error retrieving data:', error);
    }
  };

  return (
    <div className="App">
      <img src="/tao.png" alt="Tao" className="logo" />
      <div className="container">
        <div className="input-group">
          <input 
            type="text" 
            placeholder="Hash" 
            value={hash} 
            onChange={(e) => setHash(e.target.value)} 
          />
          <input 
            type="file" 
            onChange={(e) => setSelectedFile(e.target.files[0])} 
          />
        </div>
        <div className="button-group">
          <button onClick={handleStore} disabled={storing | retrieving}>{storing ? 'Storing...' : 'Store'}</button>
          <button onClick={handleRetrieve} disabled={storing | retrieving}>{retrieving ? 'Retrieving...' : 'Retrieve'}</button>
        </div>
        {response && <div className="response">Response: {JSON.stringify(response)}</div>}
      </div>
    </div>
  );
}
  




export default App;
