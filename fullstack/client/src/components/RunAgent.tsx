import React from "react";
import { TaskForm } from "./TaskForm";
import { useTask } from "@/contexts/TaskContext";
import { useNavigate } from "react-router-dom";
import { TaskRead } from "@/utils/tasks-api";

interface RunAgentProps {
  setTaskData: React.Dispatch<React.SetStateAction<TaskRead | null>>;
}

export const RunAgent: React.FC<RunAgentProps> = ({ setTaskData }) => {
  const { selectedTaskId } = useTask();
  const navigate = useNavigate();

  const handleBackToTasks = () => {
    navigate("/");
  };

  if (!selectedTaskId) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground">No task selected. Please select a task first.</p>
      </div>
    );
  }

  return <TaskForm taskId={selectedTaskId} onBack={handleBackToTasks} setTaskData={setTaskData} />;
};