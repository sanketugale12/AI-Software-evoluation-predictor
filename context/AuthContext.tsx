import React, { createContext, useContext, useReducer, useEffect, type ReactNode } from "react";
import { getAuthStatus, logout as apiLogout, setCurrentUserId, getGitHubLoginUrl } from "@/services/api";
import type { UserResponse, AuthStatusResponse } from "@/types";

type AuthState = {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
};

type AuthAction =
  | { type: "SET_USER"; payload: UserResponse | null }
  | { type: "SET_LOADING"; payload: boolean }
  | { type: "SET_ERROR"; payload: string | null }
  | { type: "LOGOUT" };

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case "SET_USER":
      return {
        ...state,
        user: action.payload,
        isAuthenticated: !!action.payload,
        isLoading: false,
      };
    case "SET_LOADING":
      return { ...state, isLoading: action.payload };
    case "SET_ERROR":
      return { ...state, error: action.payload, isLoading: false };
    case "LOGOUT":
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
      };
    default:
      return state;
  }
}

interface AuthContextType extends AuthState {
  checkAuth: () => Promise<void>;
  login: () => void;
  logout: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  const checkAuth = async () => {
    dispatch({ type: "SET_LOADING", payload: true });
    try {
      const response = await getAuthStatus();
      if (response.authenticated && response.user) {
        setCurrentUserId(response.user.id);
        dispatch({ type: "SET_USER", payload: response.user });
      } else {
        setCurrentUserId(null);
        dispatch({ type: "SET_USER", payload: null });
      }
    } catch (error) {
      setCurrentUserId(null);
      dispatch({ type: "SET_USER", payload: null });
    }
  };

  const login = () => {
    const authUrl = getGitHubLoginUrl();
    // Open in new tab for OAuth flow
    window.open(authUrl, "_blank", "width=600,height=700");
  };

  const logout = async () => {
    try {
      await apiLogout();
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      setCurrentUserId(null);
      dispatch({ type: "LOGOUT" });
    }
  };

  const clearError = () => {
    dispatch({ type: "SET_ERROR", payload: null });
  };

  // Check auth on mount
  useEffect(() => {
    checkAuth();
  }, []);

  return (
    <AuthContext.Provider
      value={{
        ...state,
        checkAuth,
        login,
        logout,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}