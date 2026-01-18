import React, { useState, useEffect } from 'react';
import './App.css';
import authService from './authService';
import Login from './components/Login';
import Register from './components/Register';
import Dashboard from './components/Dashboard';
import PasswordForm from './components/PasswordForm';
import PasswordView from './components/PasswordView';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [currentView, setCurrentView] = useState('login');
  const [selectedPassword, setSelectedPassword] = useState(null);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const authenticated = await authService.isAuthenticated();
    setIsAuthenticated(authenticated);
    if (authenticated) {
      setCurrentView('dashboard');
    }
    setIsLoading(false);
  };

  const handleLogin = () => {
    setIsAuthenticated(true);
    setCurrentView('dashboard');
  };

  const handleLogout = () => {
    authService.signOut();
    setIsAuthenticated(false);
    setCurrentView('login');
  };

  const handleViewChange = (view, password = null) => {
    setCurrentView(view);
    setSelectedPassword(password);
  };

  if (isLoading) {
    return (
      <div className="loading">
        <h2>Loading...</h2>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="app">
        {currentView === 'login' ? (
          <Login 
            onLoginSuccess={handleLogin}
            onSwitchToRegister={() => setCurrentView('register')}
          />
        ) : (
          <Register
            onRegisterSuccess={() => setCurrentView('login')}
            onSwitchToLogin={() => setCurrentView('login')}
          />
        )}
      </div>
    );
  }

  return (
    <div className="app">
      <nav className="navbar">
        <div className="navbar-content">
          <h1>🔐 Secure Password Manager</h1>
          <div className="navbar-actions">
            <button onClick={handleLogout}>Logout</button>
          </div>
        </div>
      </nav>

      <div className="container">
        {currentView === 'dashboard' && (
          <Dashboard onViewChange={handleViewChange} />
        )}
        {currentView === 'create' && (
          <PasswordForm
            onCancel={() => handleViewChange('dashboard')}
            onSuccess={() => handleViewChange('dashboard')}
          />
        )}
        {currentView === 'edit' && selectedPassword && (
          <PasswordForm
            password={selectedPassword}
            onCancel={() => handleViewChange('dashboard')}
            onSuccess={() => handleViewChange('dashboard')}
          />
        )}
        {currentView === 'view' && selectedPassword && (
          <PasswordView
            password={selectedPassword}
            onBack={() => handleViewChange('dashboard')}
            onEdit={() => handleViewChange('edit', selectedPassword)}
          />
        )}
      </div>
    </div>
  );
}

export default App;
