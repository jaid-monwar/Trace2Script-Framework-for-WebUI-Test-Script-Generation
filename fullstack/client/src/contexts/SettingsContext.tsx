import React, { createContext, useContext, useState } from 'react';

interface AgentSettings {
  llmProvider: string;
  llmModel: string;
  temperature: number;
  useVision: boolean;
  ollamaContextLength?: number;
  baseUrl: string;
  apiKey: string;
}

interface BrowserSettings {
  keepBrowserOpen: boolean;
  headlessMode: boolean;
  disableSecurity: boolean;
  windowWidth: number;
  windowHeight: number;
}

interface Settings {
  agent: AgentSettings;
  browser: BrowserSettings;
}

interface SettingsContextType {
  settings: Settings;
  updateAgentSettings: (settings: Partial<AgentSettings>) => void;
  updateBrowserSettings: (settings: Partial<BrowserSettings>) => void;
  getSettingsForAPI: () => any;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};

interface SettingsProviderProps {
  children: React.ReactNode;
}

export const SettingsProvider: React.FC<SettingsProviderProps> = ({ children }) => {
  const [settings, setSettings] = useState<Settings>({
    agent: {
      llmProvider: 'openai',
      llmModel: 'gpt-4o',
      temperature: 0.6,
      useVision: true,
      ollamaContextLength: 16000,
      baseUrl: '',
      apiKey: '',
    },
    browser: {
      keepBrowserOpen: true,
      headlessMode: false,
      disableSecurity: true,
      windowWidth: 1280,
      windowHeight: 720,
    },
  });

  const updateAgentSettings = (newSettings: Partial<AgentSettings>) => {
    setSettings(prev => ({
      ...prev,
      agent: {
        ...prev.agent,
        ...newSettings,
      },
    }));
  };

  const updateBrowserSettings = (newSettings: Partial<BrowserSettings>) => {
    setSettings(prev => ({
      ...prev,
      browser: {
        ...prev.browser,
        ...newSettings,
      },
    }));
  };

  const getSettingsForAPI = () => {
    return {
      llm_provider: settings.agent.llmProvider,
      llm_model: settings.agent.llmModel,
      temperature: settings.agent.temperature,
      use_vision: settings.agent.useVision,
      ollama_context_length: settings.agent.ollamaContextLength,
      base_url: settings.agent.baseUrl,
      api_key: settings.agent.apiKey,
      browser_headless_mode: settings.browser.headlessMode,
      disable_security: settings.browser.disableSecurity,
      window_width: settings.browser.windowWidth,
      window_height: settings.browser.windowHeight,
    };
  };

  const value: SettingsContextType = {
    settings,
    updateAgentSettings,
    updateBrowserSettings,
    getSettingsForAPI,
  };

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
}; 