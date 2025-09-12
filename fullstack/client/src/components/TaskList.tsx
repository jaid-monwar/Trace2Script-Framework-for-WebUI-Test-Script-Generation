import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertTriangle, Plus, Loader2, Trash2 } from "lucide-react";
import { getTasks, createTask, deleteTask, TaskSummary } from "@/utils/tasks-api";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface TaskListProps {
  onTaskSelect: (taskId: number) => void;
}

export const TaskList: React.FC<TaskListProps> = ({ onTaskSelect }) => {
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newTaskName, setNewTaskName] = useState("");
  const [creatingTask, setCreatingTask] = useState(false);
  const [createError, setCreateError] = useState("");
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [taskToDelete, setTaskToDelete] = useState<TaskSummary | null>(null);
  const [deletingTask, setDeletingTask] = useState(false);
  const [deleteError, setDeleteError] = useState("");

  useEffect(() => {
    fetchTasks();
  }, []);

  // Auto-hide delete error after 3 seconds
  useEffect(() => {
    if (deleteError) {
      const timer = setTimeout(() => {
        setDeleteError("");
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [deleteError]);

  const fetchTasks = async () => {
    setLoading(true);
    setError("");
    
    try {
      const result = await getTasks();
      
      if ('error' in result) {
        setError(result.error);
      } else {
        setTasks(result);
      }
    } catch (err) {
      setError("Failed to fetch tasks");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTask = async () => {
    if (!newTaskName.trim()) {
      setCreateError("Task name is required");
      return;
    }

    setCreatingTask(true);
    setCreateError("");

    try {
      const result = await createTask(newTaskName.trim());

      if ('error' in result) {
        setCreateError(result.error);
      } else {
        // Add the new task to the list
        setTasks(prev => [...prev, {
          id: result.id,
          task_name: result.task_name,
          status: result.status
        }]);
        
        // Reset form
        setNewTaskName("");
        setShowCreateForm(false);
      }
    } catch (err) {
      setCreateError("Failed to create task");
    } finally {
      setCreatingTask(false);
    }
  };

  const handleTaskClick = (taskId: number) => {
    onTaskSelect(taskId);
  };

  const handleDeleteClick = (e: React.MouseEvent, task: TaskSummary) => {
    e.stopPropagation(); // Prevent triggering the task selection
    setTaskToDelete(task);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!taskToDelete) return;

    setDeletingTask(true);
    setDeleteError("");

    try {
      const result = await deleteTask(taskToDelete.id);

      if ('error' in result) {
        setDeleteError(result.error);
      } else {
        // Remove the task from the list
        setTasks(prev => prev.filter(task => task.id !== taskToDelete.id));
      }
    } catch (err) {
      setDeleteError("An unexpected error occurred while deleting the task.");
    } finally {
      setDeletingTask(false);
      setDeleteDialogOpen(false);
      setTaskToDelete(null);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setTaskToDelete(null);
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-32">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span className="ml-2">Loading tasks...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Create Task Button */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Tasks</h2>
        <Button 
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Create Task
        </Button>
      </div>

      {/* Create Task Form */}
      {showCreateForm && (
        <Card>
          <CardHeader>
            <CardTitle>Create New Task</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="new-task-name">Task Name</Label>
              <Input
                id="new-task-name"
                value={newTaskName}
                onChange={(e) => setNewTaskName(e.target.value)}
                placeholder="Enter task name..."
                disabled={creatingTask}
              />
            </div>
            
            {createError && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>{createError}</AlertDescription>
              </Alert>
            )}

            <div className="flex gap-2">
              <Button 
                onClick={handleCreateTask}
                disabled={creatingTask || !newTaskName.trim()}
                className="flex items-center gap-2"
              >
                {creatingTask ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4" />
                    Create Task
                  </>
                )}
              </Button>
              <Button 
                variant="outline"
                onClick={() => {
                  setShowCreateForm(false);
                  setNewTaskName("");
                  setCreateError("");
                }}
                disabled={creatingTask}
              >
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Delete Error Alert */}
      {deleteError && (
        <Alert variant="destructive" className="animate-in slide-in-from-top-2 duration-300">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{deleteError}</AlertDescription>
        </Alert>
      )}

      {/* Tasks List */}
      <Card>
        <CardContent className="pt-6">
          {tasks.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <p>No tasks found. Create your first task to get started.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {tasks.map((task) => (
                <div
                  key={task.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
                  onClick={() => handleTaskClick(task.id)}
                >
                  <div className="flex-1">
                    <h3 className="font-medium text-primary hover:underline">
                      {task.task_name}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      Status: {task.status}
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={(e) => handleDeleteClick(e, task)}
                    className="text-destructive hover:text-destructive hover:bg-destructive/10"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Task</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{taskToDelete?.task_name}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleDeleteCancel} disabled={deletingTask}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleDeleteConfirm}
              disabled={deletingTask}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deletingTask ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  Deleting...
                </>
              ) : (
                "Delete Task"
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}; 