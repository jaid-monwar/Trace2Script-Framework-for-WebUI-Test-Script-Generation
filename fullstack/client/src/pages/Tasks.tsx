import React from "react";
import { TaskList } from "@/components/TaskList";
import { useTask } from "@/contexts/TaskContext";
import { useNavigate } from "react-router-dom";

const Tasks = () => {
  const { setSelectedTaskId } = useTask();
  const navigate = useNavigate();

  const handleTaskSelect = (taskId: number) => {
    setSelectedTaskId(taskId);
    navigate(`/task/${taskId}`);
  };

  return <TaskList onTaskSelect={handleTaskSelect} />;
};

export default Tasks; 