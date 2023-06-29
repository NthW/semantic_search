import React, { useState } from 'react';

export default function Upload() {
  const [file, setFile] = useState(null);
  const [textInput, setInputText] = useState('');
  const [textSearchInput, setSearchInputText] = useState('');
  const [responseValue, setResponseText] = useState([]);
  const [loadingFileUpload, setLoadingFileUpload] = useState("Upload");
  const [loadingTextUpload, setLoadingTextUpload] = useState("Upload");
  const [loadingSearch, setLoadingSearch] = useState("Search");
  const [summary, setResponseSummary] = useState("");

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleTextInputChange = (event) => {
    setInputText(event.target.value);
  };

  const handleSearchTextInputChange = (event) => {
    setSearchInputText(event.target.value);
  };

  const handleUpload = async () => {
    try {
      setLoadingFileUpload("Loading...");
      const formData = new FormData();
      formData.append('file', file);
      var url = "http://127.0.0.1:8000/upload"
      await fetch(url, {
        method: 'POST',
        headers: {
        },
        body: formData
      })
      //alert('File uploaded successfully!');
    } catch (error) {
      console.error('Error uploading file: ', error);
    }
    setLoadingFileUpload("Upload");
  };

  const handleTextUpload = async () => {
    try {
      setLoadingTextUpload("Loading...")
      const formData = new FormData();
      formData.append('text', textInput); // Append the text to the form data
      var url = "http://127.0.0.1:8000/text_upload";
      await fetch(url, {
        method: 'POST',
        headers: {},
        body: formData,
      });
      //alert('Text uploaded successfully!');
    } catch (error) {
      console.error('Error uploading text: ', error);
    }
    setLoadingTextUpload("Upload")
  };

  const handleSearch = async () => {
    try {
      setLoadingSearch("Searching...")
      setResponseText([]);
      setResponseSummary('');
      const formData = new FormData();
      formData.append('text', textSearchInput);
      var url = "http://127.0.0.1:8000/search";
      var res = await fetch(url, {
        method: 'POST',
        headers: {},
        body: formData,
      });
      const responseJson = await res.json();
      console.log(responseJson.results);
      if (responseJson.results) {setResponseText(responseJson.results);}    
      if (responseJson.summary) {setResponseSummary(responseJson.summary);}
    } catch (error) {
      console.error('Error uploading text: ', error);
    }
    setLoadingSearch("Search")
  };

  return (
<div class="flex flex-col space-y-4 p-20">
  <h1 class="text-4xl font-bold mb-4">Semantic Search</h1>
  <hr class="border-gray-300 my-4"></hr>
  <div class="space-y-2">
    <h1 class="text-2xl font-bold">File Upload</h1>
    <input type="file" onChange={handleFileChange} class="py-2 px-4 border border-gray-300 rounded-md" />
    <button onClick={handleUpload} class="py-2 px-4 bg-blue-500 text-white rounded-md">{loadingFileUpload}</button>
  </div>
  <div class="space-y-2">
    <h1 class="text-2xl font-bold">Text Upload</h1>
    <input
      class="py-2 px-4 border border-gray-300 rounded-md"
      type="text"
      placeholder="Enter text"
      value={textInput}
      onChange={handleTextInputChange}
    />
    <button onClick={handleTextUpload} class="py-2 px-4 bg-blue-500 text-white rounded-md">{loadingTextUpload}</button>
  </div>
  <hr class="border-gray-300 my-4"></hr>
  <div class="space-y-2">
    <h1 class="text-2xl font-bold">Search</h1>
    <input
      class="py-2 px-4 border border-gray-300 rounded-md"
      type="text"
      placeholder="Enter text"
      value={textSearchInput}
      onChange={handleSearchTextInputChange}
    />
    <button onClick={handleSearch} class="py-2 px-4 bg-blue-500 text-white rounded-md">{loadingSearch}</button>
  </div>
  <div>
  {responseValue.length > 0 && (
    <>
      <h1 class="text-2xl font-bold">Semantic Result Summary</h1>
      <h2 class="py-10">{summary}</h2>
      <h1 class="text-2xl font-bold pb-8">Semantic Lookup</h1>
      <div class="max-w-full overflow-x-auto">
        <table class="table-auto">
          <thead>
            <tr>
              <th>File Name</th>
              <th>Text</th>
              <th>Line in File</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            {responseValue.map(row => (
              <tr key={row[0]}>
                <td class="px-6 py-4 whitespace-wrap">{row[0]}</td>
                <td class="px-6 py-4 whitespace-wrap">{row[1]}</td>
                <td class="px-6 py-4 whitespace-nowrap">{row[2]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )}



  </div>
  
</div>

  );
}
