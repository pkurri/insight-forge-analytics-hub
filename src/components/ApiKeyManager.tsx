import React, { useState } from 'react';
import { useApiKey } from '../hooks/useApiKey';

export const ApiKeyManager: React.FC = () => {
  const { apiKey, saveApiKey, removeApiKey } = useApiKey();
  const [newApiKey, setNewApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);

  const handleSave = () => {
    if (newApiKey.trim()) {
      saveApiKey(newApiKey.trim());
      setNewApiKey('');
    }
  };

  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <h2 className="text-lg font-semibold mb-4">API Key Management</h2>
      
      {apiKey ? (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Current API Key</label>
            <div className="mt-1 flex items-center space-x-2">
              <input
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                readOnly
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
              />
              <button
                onClick={() => setShowKey(!showKey)}
                className="px-3 py-2 text-sm text-gray-600 hover:text-gray-800"
              >
                {showKey ? 'Hide' : 'Show'}
              </button>
            </div>
          </div>
          <button
            onClick={removeApiKey}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
          >
            Remove API Key
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Enter New API Key</label>
            <div className="mt-1">
              <input
                type="password"
                value={newApiKey}
                onChange={(e) => setNewApiKey(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="Enter your API key"
              />
            </div>
          </div>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Save API Key
          </button>
        </div>
      )}
    </div>
  );
}; 