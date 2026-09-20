import React, { useState } from 'react';
import { analyzePR, resolveIssueContext, getOpsContext, askAssistant } from '../services/index';

export const SidePanel = () => {
  const [view, setView] = useState('metadata');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  const runAnalysis = async (type: string, arg: string) => {
    setLoading(true);
    try {
      let res = '';
      if (type === 'pr') res = await analyzePR(arg);
      else if (type === 'issue') res = await resolveIssueContext(arg);
      else if (type === 'ops') res = await getOpsContext();
      else if (type === 'ask') res = await askAssistant(arg);
      setResult(res);
    } catch (e) {
      setResult('Error running analysis');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '1rem', fontFamily: 'sans-serif' }}>
      <h2 style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>ASEP Intelligence</h2>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '1rem', borderBottom: '1px solid #ccc', paddingBottom: '5px' }}>
        <button onClick={() => setView('metadata')}>Repo</button>
        <button onClick={() => setView('analysis')}>Analysis</button>
        <button onClick={() => setView('assistant')}>Assistant</button>
      </div>

      <div>
        {view === 'metadata' && <div>Repository Metadata View (Ready)</div>}
        {view === 'analysis' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <input id="arg" placeholder="PR # or Issue #" style={{ border: '1px solid #ccc', padding: '4px' }} />
            <button onClick={() => runAnalysis('pr', (document.getElementById('arg') as HTMLInputElement).value)}>Analyze PR</button>
            <button onClick={() => runAnalysis('issue', (document.getElementById('arg') as HTMLInputElement).value)}>Analyze Issue</button>
            <button onClick={() => runAnalysis('ops', '')}>Ops Context</button>
            {loading && <div>Analyzing...</div>}
            <div style={{ marginTop: '10px', background: '#f0f0f0', padding: '10px', fontSize: '0.9rem', whiteSpace: 'pre-wrap' }}>{result}</div>
          </div>
        )}
        {view === 'assistant' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <input id="q" placeholder="Ask anything..." style={{ border: '1px solid #ccc', padding: '4px' }} />
            <button onClick={() => runAnalysis('ask', (document.getElementById('q') as HTMLInputElement).value)}>Ask</button>
            <div style={{ marginTop: '10px', background: '#f0f0f0', padding: '10px', fontSize: '0.9rem', whiteSpace: 'pre-wrap' }}>{result}</div>
          </div>
        )}
      </div>
    </div>
  );
};
