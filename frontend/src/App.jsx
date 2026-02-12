import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import { AgGridReact } from 'ag-grid-react';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import { JsonView, darkStyles } from 'react-json-view-lite';
import 'react-json-view-lite/dist/index.css';
import { Calendar, Filter, Key, RefreshCw, X } from 'lucide-react';

const App = () => {
  const [rowData, setRowData] = useState([]);
  const [token, setToken] = useState(localStorage.getItem('doc_processor_token') || '');
  const [dateFilter, setDateFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedJson, setSelectedJson] = useState(null);
  const [error, setError] = useState(null);

  const columnDefs = useMemo(() => [
    { field: 'document_name', headerName: 'Document Name', flex: 2, sortable: true, filter: true },
    { field: 'document_type', headerName: 'Type', flex: 1, sortable: true, filter: true },
    {
      field: 'document_size',
      headerName: 'Size (KB)',
      flex: 1,
      valueFormatter: params => (params.value / 1024).toFixed(2),
      sortable: true
    },
    {
      field: 'processed_at',
      headerName: 'Processed At',
      flex: 1.5,
      sortable: true,
      valueFormatter: params => new Date(params.value).toLocaleString()
    },
    { field: 'error_message', headerName: 'Status', flex: 1.5, cellStyle: params => params.value ? { color: '#f87171' } : { color: '#4ade80' }, valueFormatter: params => params.value ? 'Error' : 'Success' }
  ], []);

  const fetchData = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('/api/documents', {
        headers: { Authorization: `Bearer ${token}` },
        params: { date: dateFilter || undefined }
      });
      setRowData(response.data);
      localStorage.setItem('doc_processor_token', token);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [token, dateFilter]);

  useEffect(() => {
    if (token) fetchData();
  }, [fetchData]);

  const onRowClicked = (event) => {
    setSelectedJson(event.data.extracted_data);
  };

  return (
    <div className="app-container">
      <header>
        <h1>Document Processor</h1>
        {loading && <RefreshCw className="animate-spin text-primary" size={24} />}
      </header>

      <div className="controls">
        <div className="control-group">
          <label><Key size={14} style={{ marginRight: '4px' }} /> Access Token</label>
          <input
            type="password"
            placeholder="gcloud auth print-access-token"
            value={token}
            onChange={(e) => setToken(e.target.value)}
          />
        </div>
        <div className="control-group">
          <label><Calendar size={14} style={{ marginRight: '4px' }} /> Processed Date</label>
          <input
            type="date"
            value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value)}
          />
        </div>
        <button onClick={fetchData} disabled={loading || !token}>
          Apply Filters
        </button>
      </div>

      {error && (
        <div style={{ color: '#f87171', marginBottom: '1rem', padding: '1rem', background: 'rgba(248, 113, 113, 0.1)', borderRadius: '0.5rem', border: '1px solid rgba(248, 113, 113, 0.2)' }}>
          {error}
        </div>
      )}

      <div className="grid-container ag-theme-alpine-dark">
        <AgGridReact
          rowData={rowData}
          columnDefs={columnDefs}
          onRowClicked={onRowClicked}
          pagination={true}
          paginationPageSize={10}
          animateRows={true}
          overlayNoRowsTemplate="<span>Use an access token to load documents</span>"
        />
      </div>

      {selectedJson && (
        <div className="modal-overlay" onClick={() => setSelectedJson(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Extracted Data</h3>
              <button className="close-btn" onClick={() => setSelectedJson(null)}>
                <X size={24} />
              </button>
            </div>
            <div className="modal-body">
              <JsonView
                data={typeof selectedJson === 'string' ? JSON.parse(selectedJson) : selectedJson}
                style={darkStyles}
                shouldExpandNode={() => true}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
