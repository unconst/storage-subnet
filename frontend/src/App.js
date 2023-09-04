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
  const [key, setKey] = useState('');
  const [data, setData] = useState('');
  const [file, setFile] = useState(null);
  const [response, setResponse] = useState(null);

  const handleStore = async () => {
    try {
      console.log('Attempting to store data with key:', key, 'and data:', data);
  
      let fileDataUrl = null;
      if (file) {
        fileDataUrl = await fileToDataUrl(file);
      }
  
      const payload = {
        key,
        data,
        file: fileDataUrl,
      };
  
      const res = await fetch(`http://0.0.0.0:8000/store/?key=${key}&data=${JSON.stringify(payload)}`);
  
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
      console.log('Attempting to retrieve data with key:', key);
      const res = await fetch(`http://0.0.0.0:8000/retrieve/?key=${key}`);
      if (!res.ok) {
        console.error('Error response from server:', res);
        return;
      }
      const result = await res.json(); // Get the response as JSON
      console.log('Server response:', result);
  
      if (result.file) {
        // Extract the base64 encoded string from the data URL
        const base64String = result.file.split(',')[1];
  
        // Decode the base64 string to a binary string
        const binaryString = atob(base64String);
  
        // Convert the binary string to a Uint8Array
        const binaryLen = binaryString.length;
        const bytes = new Uint8Array(binaryLen);
        for (let i = 0; i < binaryLen; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
  
        // Create a Blob from the Uint8Array
        const blob = new Blob([bytes], { type: 'application/octet-stream' });
  
        // Create a URL for the Blob and use it to create a download link
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'retrieved-file'; // You can change this to a more appropriate filename
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } else {
        console.log('No file found in the response');
      }
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
            placeholder="Key" 
            value={key} 
            onChange={(e) => setKey(e.target.value)} 
          />
          <input 
            type="file" 
            onChange={(e) => setFile(e.target.files[0])} 
          />
        </div>
        <div className="button-group">
          <button onClick={handleStore}>Store</button>
          <button onClick={handleRetrieve}>Retrieve</button>
        </div>
        {response && <div className="response">Response: {JSON.stringify(response)}</div>}
      </div>
    </div>
  );
}
  




export default App;
