import { CognitoUserPool, CognitoUser, AuthenticationDetails } from 'amazon-cognito-identity-js';
import config from './config';

// Initialize Cognito User Pool
const poolData = {
  UserPoolId: config.cognito.userPoolId,
  ClientId: config.cognito.userPoolWebClientId
};

const userPool = new CognitoUserPool(poolData);

class AuthService {
  /**
   * Sign up a new user
   */
  signUp(username, password, email) {
    return new Promise((resolve, reject) => {
      const attributeList = [
        {
          Name: 'email',
          Value: email
        },
        {
          Name: 'nickname',
          Value: email
        }
      ];

      userPool.signUp(username, password, attributeList, null, (err, result) => {
        if (err) {
          reject(err);
          return;
        }
        resolve(result.user);
      });
    });
  }

  /**
   * Confirm user registration with verification code
   */
  confirmRegistration(username, code) {
    return new Promise((resolve, reject) => {
      const userData = {
        Username: username,
        Pool: userPool
      };

      const cognitoUser = new CognitoUser(userData);

      cognitoUser.confirmRegistration(code, true, (err, result) => {
        if (err) {
          reject(err);
          return;
        }
        resolve(result);
      });
    });
  }

  /**
   * Sign in a user
   */
  signIn(username, password) {
    return new Promise((resolve, reject) => {
      const authenticationData = {
        Username: username,
        Password: password
      };

      const authenticationDetails = new AuthenticationDetails(authenticationData);

      const userData = {
        Username: username,
        Pool: userPool
      };

      const cognitoUser = new CognitoUser(userData);

      cognitoUser.authenticateUser(authenticationDetails, {
        onSuccess: (result) => {
          resolve({
            idToken: result.getIdToken().getJwtToken(),
            accessToken: result.getAccessToken().getJwtToken(),
            refreshToken: result.getRefreshToken().getToken()
          });
        },
        onFailure: (err) => {
          reject(err);
        },
        newPasswordRequired: (userAttributes) => {
          reject({
            code: 'NewPasswordRequired',
            message: 'New password required',
            userAttributes
          });
        }
      });
    });
  }

  /**
   * Sign out the current user
   */
  signOut() {
    const cognitoUser = userPool.getCurrentUser();
    if (cognitoUser) {
      cognitoUser.signOut();
    }
    localStorage.removeItem('idToken');
  }

  /**
   * Get the current user
   */
  getCurrentUser() {
    return userPool.getCurrentUser();
  }

  /**
   * Get current session
   */
  getSession() {
    return new Promise((resolve, reject) => {
      const cognitoUser = userPool.getCurrentUser();

      if (!cognitoUser) {
        reject(new Error('No user found'));
        return;
      }

      cognitoUser.getSession((err, session) => {
        if (err) {
          reject(err);
          return;
        }
        resolve(session);
      });
    });
  }

  /**
   * Get the ID token for API calls
   */
  async getIdToken() {
    try {
      const session = await this.getSession();
      return session.getIdToken().getJwtToken();
    } catch (error) {
      return null;
    }
  }

  /**
   * Check if user is authenticated
   */
  async isAuthenticated() {
    try {
      await this.getSession();
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Change password for current user
   */
  changePassword(oldPassword, newPassword) {
    return new Promise((resolve, reject) => {
      const cognitoUser = userPool.getCurrentUser();

      if (!cognitoUser) {
        reject(new Error('No user found'));
        return;
      }

      cognitoUser.getSession((err, session) => {
        if (err) {
          reject(err);
          return;
        }

        cognitoUser.changePassword(oldPassword, newPassword, (err, result) => {
          if (err) {
            reject(err);
            return;
          }
          resolve(result);
        });
      });
    });
  }

  /**
   * Initiate forgot password flow
   */
  forgotPassword(username) {
    return new Promise((resolve, reject) => {
      const userData = {
        Username: username,
        Pool: userPool
      };

      const cognitoUser = new CognitoUser(userData);

      cognitoUser.forgotPassword({
        onSuccess: (result) => {
          resolve(result);
        },
        onFailure: (err) => {
          reject(err);
        }
      });
    });
  }

  /**
   * Confirm new password with verification code
   */
  confirmPassword(username, verificationCode, newPassword) {
    return new Promise((resolve, reject) => {
      const userData = {
        Username: username,
        Pool: userPool
      };

      const cognitoUser = new CognitoUser(userData);

      cognitoUser.confirmPassword(verificationCode, newPassword, {
        onSuccess: () => {
          resolve('Password confirmed');
        },
        onFailure: (err) => {
          reject(err);
        }
      });
    });
  }
}

export default new AuthService();
