import React, { useState, useEffect } from 'react';
import apiService from '../apiService';

function PasswordForm({ password, onCancel, onSuccess }) {
  const [siteName, setSiteName] = useState('');
  const [siteUrl, setSiteUrl] = useState('');
  const [username, setUsername] = useState('');
  const [passwordValue, setPasswordValue] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const isEditMode = !!password;

  useEffect(() => {
    if (password) {
      setSiteName(password.site_name || '');
      setSiteUrl(password.site_url || '');
      setUsername(password.username || '');
      setNotes(password.notes || '');
    }
  }, [password]);

  const generatePassword = () => {
    const length = 16;
    const charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*';
    let password = '';
    for (let i = 0; i < length; i++) {
      password += charset.charAt(Math.floor(Math.random() * charset.length));
    }
    setPasswordValue(password);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    if (!siteName || !username) {
      setError('Site name and username are required');
      setIsLoading(false);
      return;
    }

    if (!isEditMode && !passwordValue) {
      setError('Password is required');
      setIsLoading(false);
      return;
    }

    const data = {
      site_name: siteName,
      site_url: siteUrl,
      username: username,
      notes: notes
    };

    // Only include password if it's been entered
    if (passwordValue) {
      data.password = passwordValue;
    }

    try {
      if (isEditMode) {
        await apiService.updatePassword(password.password_id, data);
      } else {
        await apiService.createPassword(data);
      }
      onSuccess();
    } catch (err) {
      console.error('Error saving password:', err);
      setError(err.response?.data?.error || 'Failed to save password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="password-view">
      <h2>{isEditMode ? 'Edit Password' : 'Add New Password'}</h2>
      {error && <div className="alert alert-error">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="siteName">Site Name *</label>
          <input
            type="text"
            id="siteName"
            value={siteName}
            onChange={(e) => setSiteName(e.target.value)}
            required
            placeholder="e.g., Gmail, Facebook"
          />
        </div>

        <div className="form-group">
          <label htmlFor="siteUrl">Site URL</label>
          <input
            type="url"
            id="siteUrl"
            value={siteUrl}
            onChange={(e) => setSiteUrl(e.target.value)}
            placeholder="https://example.com"
          />
        </div>

        <div className="form-group">
          <label htmlFor="username">Username *</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            placeholder="email@example.com or username"
          />
        </div>

        <div className="form-group">
          <label htmlFor="password">
            Password {isEditMode && '(leave blank to keep current)'}
          </label>
          <div className="password-display">
            <input
              type="text"
              id="password"
              value={passwordValue}
              onChange={(e) => setPasswordValue(e.target.value)}
              placeholder="Enter password"
            />
            <button
              type="button"
              className="btn btn-secondary"
              onClick={generatePassword}
            >
              Generate
            </button>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="notes">Notes</label>
          <textarea
            id="notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Additional notes (optional)"
          />
        </div>

        <div className="password-actions">
          <button type="submit" className="btn btn-primary" disabled={isLoading}>
            {isLoading ? 'Saving...' : (isEditMode ? 'Update' : 'Save')}
          </button>
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

export default PasswordForm;
