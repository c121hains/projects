import React, { useState, useEffect } from 'react';
import apiService from '../apiService';

function Dashboard({ onViewChange }) {
  const [passwords, setPasswords] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadPasswords();
  }, []);

  const loadPasswords = async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await apiService.getPasswords();
      setPasswords(data);
    } catch (err) {
      console.error('Error loading passwords:', err);
      setError('Failed to load passwords. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this password?')) {
      return;
    }

    try {
      await apiService.deletePassword(id);
      setPasswords(passwords.filter(p => p.password_id !== id));
    } catch (err) {
      console.error('Error deleting password:', err);
      alert('Failed to delete password. Please try again.');
    }
  };

  if (isLoading) {
    return <div className="loading">Loading passwords...</div>;
  }

  return (
    <div>
      <div className="password-list-header">
        <h2>My Passwords</h2>
        <button 
          className="btn btn-primary"
          onClick={() => onViewChange('create')}
        >
          + Add Password
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {passwords.length === 0 ? (
        <div className="empty-state">
          <h3>No passwords saved yet</h3>
          <p>Click "Add Password" to get started</p>
        </div>
      ) : (
        <div className="password-grid">
          {passwords.map((password) => (
            <div key={password.password_id} className="password-card">
              <h3>{password.site_name}</h3>
              <div className="password-card-info">
                <p><strong>Username:</strong> {password.username}</p>
                {password.site_url && (
                  <p><strong>URL:</strong> {password.site_url}</p>
                )}
              </div>
              <div className="password-card-actions">
                <button
                  className="btn btn-primary"
                  onClick={() => onViewChange('view', password)}
                >
                  View
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={() => onViewChange('edit', password)}
                >
                  Edit
                </button>
                <button
                  className="btn btn-danger"
                  onClick={() => handleDelete(password.password_id)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Dashboard;
