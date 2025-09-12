import React, { createContext, useContext, useEffect, useState } from 'react';
import { getToken, getMe } from '@/utils/auth-api';

interface AuthContextType {
  isAuthenticated: boolean;
  user: any | null;
  login: (username: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    const token = localStorage.getItem('atsg_jwt');
    if (token) {
      try {
        const userData = await getMe();
        if (!userData.error) {
          setUser(userData);
          setIsAuthenticated(true);
        } else {
          localStorage.removeItem('atsg_jwt');
          setIsAuthenticated(false);
          setUser(null);
        }
      } catch (error) {
        localStorage.removeItem('atsg_jwt');
        setIsAuthenticated(false);
        setUser(null);
      }
    }
    setLoading(false);
  };

  const login = async (username: string, password: string) => {
    try {
      const result = await getToken(username, password);
      
      if (result.error) {
        return { success: false, error: result.error };
      }

      if (result.access_token) {
        localStorage.setItem('atsg_jwt', result.access_token);
        setIsAuthenticated(true);
        
        const userData = await getMe();
        if (!userData.error) {
          setUser(userData);
        }
        
        return { success: true };
      }
      
      return { success: false, error: 'Login failed' };
    } catch (error) {
      return { success: false, error: 'An unexpected error occurred' };
    }
  };

  const logout = () => {
    localStorage.removeItem('atsg_jwt');
    setIsAuthenticated(false);
    setUser(null);
  };

  const value: AuthContextType = {
    isAuthenticated,
    user,
    login,
    logout,
    loading,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 