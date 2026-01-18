import React, { useState } from 'react';
import apiService from '../apiService';

function PasswordView({ password, onBack, onEdit }) {
  const [decryptedPassword, setDecryptedPassword] = useState('');
  const [isRevealed, setIsRevealed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleRevealPassword = async () => {
    if (isRevealed) {
      setIsRevealed(false);
      setDecryptedPassword('');
      return;
    }

    setIsLoading(true);
    setError('');
    try {
      const decrypted = await apiService.decryptPassword(password.password_id);
      setDecryptedPassword(decrypted);
      setIsRevealed(true);
    } catch (err) {
      console.error('Error decrypting password:', err);
      setError('Failed to decrypt password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyPassword = () => {
    if (decryptedPassword) {
      navigator.clipboard.writeText(decryptedPassword);
      alert('Password copied to clipboard!');
    }
  };

  return (
    <div className="password-view">
      <h2>{password.site_name}</h2>

      {error && <div className="alert alert-error">{error}</div>}

      {password.site_url && (
        <div className="password-detail">
          <label>Site URL</label>
          <div className="password-detail-value">
            <a href={password.site_url} target="_blank" rel="noopener noreferrer">
              {password.site_url}
            </a>
          </div>
        </div>
      )}

      <div className="password-detail">
        <label>Username</label>
        <div className="password-detail-value">{password.username}</div>
      </div>

      <div className="password-detail">
        <label>Password</label>
        <div className="password-display">
          <input
            type={isRevealed ? 'text' : 'password'}
            value={isRevealed ? decryptedPassword : '••••••••'}
            readOnly
          />
          <button
            className="btn btn-secondary"
            onClick={handleRevealPassword}
            disabled={isLoading}
          >
            {isLoading ? 'Loading...' : (isRevealed ? 'Hide' : 'Reveal')}
          </button>
          {isRevealed && (
            <button
              className="btn btn-primary"
              onClick={handleCopyPassword}
            >
              Copy
            </button>
          )}
        </div>
      </div>

      {password.notes && (
        <div className="password-detail">
          <label>Notes</label>
          <div className="password-detail-value">{password.notes}</div>
        </div>
      )}

      <div className="password-detail">
        <label>Created</label>
        <div className="password-detail-value">
          {new Date(password.created_at).toLocaleString()}
        </div>
      </div>

      {password.updated_at && (
        <div className="password-detail">
          <label>Last Updated</label>
          <div className="password-detail-value">
            {new Date(password.updated_at).toLocaleString()}
          </div>
        </div>
      )}

      <div className="password-actions">
        <button className="btn btn-primary" onClick={onEdit}>
          Edit
        </button>
        <button className="btn btn-secondary" onClick={onBack}>
          Back to List
        </button>
      </div>
    </div>
  );
}

export default PasswordView;
