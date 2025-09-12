import React, { createContext, useContext, useState, ReactNode } from 'react';

interface TaskContextType {
  selectedTaskId: number | null;
  setSelectedTaskId: (taskId: number | null) => void;
}

const TaskContext = createContext<TaskContextType | undefined>(undefined);

interface TaskProviderProps {
  children: ReactNode;
}

export const TaskProvider: React.FC<TaskProviderProps> = ({ children }) => {
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null);

  return (
    <TaskContext.Provider value={{ selectedTaskId, setSelectedTaskId }}>
      {children}
    </TaskContext.Provider>
  );
};

export const useTask = () => {
  const context = useContext(TaskContext);
  if (context === undefined) {
    throw new Error('useTask must be used within a TaskProvider');
  }
  return context;
}; 