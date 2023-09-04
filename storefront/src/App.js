import React, { useState } from 'react';
import './App.css';

function App() {
  const [key, setKey] = useState('');
  const [data, setData] = useState('');
  const [response, setResponse] = useState(null);

  const handleStore = async () => {
    try {
      console.log('Attempting to store data with key:', key, 'and data:', data);
      const res = await fetch(`http://0.0.0.0:8000/store/?key=${key}&data=${data}`);
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
      const result = await res.json();
      console.log('Server response:', result);
      setResponse(result);
    } catch (error) {
      console.error('Error retrieving data:', error);
    }
  };

  return (
    <div className="App">
      <input 
        type="text" 
        placeholder="Key" 
        value={key} 
        onChange={(e) => setKey(e.target.value)} 
      />
      <input 
        type="text" 
        placeholder="Data" 
        value={data} 
        onChange={(e) => setData(e.target.value)} 
      />
      <button onClick={handleStore}>Store</button>
      <button onClick={handleRetrieve}>Retrieve</button>
      {response && <div>{JSON.stringify(response)}</div>}
    </div>
  );
}

export default App;
