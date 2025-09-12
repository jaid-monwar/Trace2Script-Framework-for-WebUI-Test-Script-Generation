import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Square, Pause, Eraser, FileText, Send, Download, ArrowLeft, Loader2 } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertTriangle } from "lucide-react";
import {
  getTask,
  initiateTask,
  getTaskResult,
  TaskRead,
  TaskInitiate,
  TaskResult
} from "@/utils/tasks-api";
import { useSettings } from "@/contexts/SettingsContext";
import { encryptApiKey } from "@/utils/encryption";

interface TaskFormProps {
  taskId: number;
  onBack: () => void;
  setTaskData: React.Dispatch<React.SetStateAction<TaskRead | null>>;
}

export const TaskForm: React.FC<TaskFormProps> = ({ taskId, onBack, setTaskData }) => {
  const [task, setTask] = useState<TaskRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Form fields
  const [taskName, setTaskName] = useState("");
  const [instruction, setInstruction] = useState("");
  const [description, setDescription] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [action, setAction] = useState("");
  const [expectedOutcome, setExpectedOutcome] = useState("");
  const [expectedStatus, setExpectedStatus] = useState("");
  const [apiKey, setApiKey] = useState("");

  // Window dimensions from task
  const [windowWidth, setWindowWidth] = useState(1280);
  const [windowHeight, setWindowHeight] = useState(720);

  // UI states
  const [userInput, setUserInput] = useState("");
  const [showWarning, setShowWarning] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [apiResponse, setApiResponse] = useState<any>(null);
  const [taskResult, setTaskResult] = useState<TaskResult | null>(null);
  const [resultLoading, setResultLoading] = useState(false);

  const { updateAgentSettings, updateBrowserSettings, settings } = useSettings();

  // Auto-hide success message after 3 seconds
  useEffect(() => {
    if (submitSuccess) {
      const timer = setTimeout(() => {
        setSubmitSuccess(false);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [submitSuccess]);

  useEffect(() => {
    fetchTask();
  }, [taskId]);

  // Fetch task result when task status is completed
  useEffect(() => {
    const fetchTaskResult = async () => {
      if (task && task.status === 'completed') {
        setResultLoading(true);
        try {
          const result = await getTaskResult(taskId);
          if ('error' in result) {
            console.error("Failed to fetch task result:", result.error);
          } else {
            setTaskResult(result);
          }
        } catch (err) {
          console.error("Failed to fetch task result:", err);
        } finally {
          setResultLoading(false);
        }
      }
    };

    fetchTaskResult();
  }, [task?.status, taskId]);

  const fetchTask = async () => {
    setLoading(true);
    setError("");

    try {
      const result = await getTask(taskId);

      if ('error' in result) {
        setError(result.error);
      } else {
        setTask(result);
        populateForm(result);
      }
    } catch (err) {
      setError("Failed to fetch task");
    } finally {
      setLoading(false);
    }
  };

  const populateForm = (taskData: TaskRead) => {
    setTaskName(taskData.task_name || "");
    setInstruction(taskData.instruction || "");
    setDescription(taskData.description || "");
    setSearchInput(taskData.search_input_input || "");
    setAction(taskData.search_input_action || "");
    setExpectedOutcome(taskData.expected_outcome || "");
    setExpectedStatus(taskData.expected_status || "");

    // Set window dimensions from task data
    setWindowWidth(taskData.window_width || 1280);
    setWindowHeight(taskData.window_height || 720);

    // Update global agent settings
    updateAgentSettings({
      llmProvider: taskData.llm_provider || "openai",
      llmModel: taskData.llm_model || "gpt-4o",
      temperature: taskData.temperature || 0.6,
      ollamaContextLength: taskData.context_length || 16000,
      baseUrl: taskData.base_url || "",
      apiKey: taskData.api_key || "",
    });

    // Update global browser settings
    updateBrowserSettings({
      headlessMode: taskData.browser_headless_mode ?? true,
      disableSecurity: taskData.disable_security ?? true,
      windowWidth: taskData.window_width || 1280,
      windowHeight: taskData.window_height || 720,
    });
  };

  const handleSubmitTask = async () => {
    if (!taskName.trim() || !instruction.trim()) {
      setShowWarning(true);
      return;
    }

    setShowWarning(false);
    setSubmitError("");
    setSubmitSuccess(false);
    setApiResponse(null);
    setIsSubmitting(true);

    try {
      // Determine which API key to use
      let finalApiKey = "";
      if (apiKey.trim()) {
        // If user provided an API key in the form, encrypt and use it
        finalApiKey = encryptApiKey(apiKey);
      } else {
        // If no API key in form, try to get encrypted key from localStorage
        const storedEncryptedKey = localStorage.getItem('encrypted_api_key');
        if (storedEncryptedKey) {
          finalApiKey = storedEncryptedKey;
        }
      }

      const taskData: TaskInitiate = {
        instruction: instruction,
        description: description,
        search_input_input: searchInput,
        search_input_action: action,
        expected_outcome: expectedOutcome,
        expected_status: expectedStatus,
        ...(finalApiKey && { api_key: finalApiKey }),
      };

      const result = await initiateTask(taskId, taskData);

      if ('error' in result) {
        setSubmitError(result.error);
      } else {
        setSubmitSuccess(true);
        setTask(result);
        setTaskData(result);
        setApiResponse(result);
        console.log("Task initiated successfully:", result);
      }
    } catch (error) {
      setSubmitError("An unexpected error occurred while submitting the task.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClear = () => {
    setApiResponse(null);
    setSubmitSuccess(false);
    setSubmitError("");
  };

  const handleDownloadScript = () => {
    if (taskResult?.result_json_url) {
      // Create a temporary anchor element to trigger download
      const link = document.createElement('a');
      link.href = taskResult.result_json_url;
      link.download = `task_${taskId}.py`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  // Function to format JSON with syntax highlighting
  const formatJSON = (obj: any): string => {
    const jsonString = JSON.stringify(obj, null, 2);
    return jsonString
      .replace(/"([^"]+)":/g, '<span class="text-blue-600 dark:text-blue-400">"$1"</span>:')
      .replace(/: "([^"]*)"/g, ': <span class="text-green-600 dark:text-green-400">"$1"</span>')
      .replace(/: (\d+)/g, ': <span class="text-orange-600 dark:text-orange-400">$1</span>')
      .replace(/: (true|false|null)/g, ': <span class="text-purple-600 dark:text-purple-400">$1</span>');
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-32">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span className="ml-2">Loading task...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <Button variant="outline" onClick={onBack} className="flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" />
          Back to Tasks
        </Button>
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className={`space-y-6 transition-all duration-500 ${isSubmitting ? 'animate-pulse' : ''}`}>
      {/* Back Button */}
      <div className={`transition-all duration-500 ${isSubmitting ? 'border-2 border-teal-500 rounded-lg p-2 shadow-lg shadow-teal-500/20' : ''}`}>
        <Button variant="outline" onClick={onBack} className="flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" />
          Back to Tasks
        </Button>
      </div>

      {/* Agent Interaction */}
      {/* <div className={`transition-all duration-500 ${isSubmitting ? 'border-2 border-teal-500 rounded-lg p-2 shadow-lg shadow-teal-500/20' : ''}`}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="w-2 h-2 bg-muted rounded-full"></span>
              Agent Interaction
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className="w-full bg-muted/20 rounded border-2 border-dashed border-muted-foreground/20 flex items-center justify-center"
              style={{
                aspectRatio: `${settings.browser.windowWidth}/${settings.browser.windowHeight}`,
                width: '100%',
                height: 'auto'
              }}
            >
              <p className="text-muted-foreground">Agent interaction will appear here</p>
            </div>
          </CardContent>
        </Card>
      </div> */}

      {/* User Input */}
      {/* <div className={`transition-all duration-500 ${isSubmitting ? 'border-2 border-teal-500 rounded-lg p-2 shadow-lg shadow-teal-500/20' : ''}`}>
        <Card>
          <CardContent className="p-6">
            <div className="space-y-2">
              <Label htmlFor="user-input">User Input</Label>
              <Input
                id="user-input"
                placeholder="Enter your next task..."
                value={userInput || ""}
                onChange={(e) => setUserInput(e.target.value)}
              />
            </div>
          </CardContent>
        </Card>
      </div> */}

      {/* Test Case Configuration */}
      <div className={`transition-all duration-500 ${isSubmitting ? 'border-2 border-teal-500 rounded-lg p-2 shadow-lg shadow-teal-500/20' : ''}`}>
        <Card>
          <CardHeader>
            <CardTitle>Test Case Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Task Name */}
            <div className="space-y-2">
              <Label htmlFor="task-name">Task Name</Label>
              <Input
                id="task-name"
                value={taskName || ""}
                onChange={(e) => setTaskName(e.target.value)}
              />
            </div>

            {/* Instruction */}
            <div className="space-y-2">
              <Label htmlFor="instruction">Instruction</Label>
              <Textarea
                id="instruction"
                value={instruction || ""}
                onChange={(e) => setInstruction(e.target.value)}
                rows={3}
              />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={description || ""}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
              />
            </div>

            {/* Input Parameters Section */}
            <div className="space-y-4">
              <Label className="text-base font-semibold">Input Parameters</Label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Search Input */}
                <div className="space-y-2">
                  <Label htmlFor="search-input">Search Input</Label>
                  <Input
                    id="search-input"
                    value={searchInput || ""}
                    onChange={(e) => setSearchInput(e.target.value)}
                  />
                </div>

                {/* Action */}
                <div className="space-y-2">
                  <Label htmlFor="action">Action</Label>
                  <Input
                    id="action"
                    value={action || ""}
                    onChange={(e) => setAction(e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* Expected Results Section */}
            <div className="space-y-4">
              <Label className="text-base font-semibold">Expected Results</Label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Expected Outcome */}
                <div className="space-y-2">
                  <Label htmlFor="expected-outcome">Expected Outcome</Label>
                  <Textarea
                    id="expected-outcome"
                    value={expectedOutcome || ""}
                    onChange={(e) => setExpectedOutcome(e.target.value)}
                    rows={3}
                  />
                </div>

                {/* Expected Status */}
                <div className="space-y-2">
                  <Label htmlFor="expected-status">Expected Status</Label>
                  <Input
                    id="expected-status"
                    value={expectedStatus || ""}
                    onChange={(e) => setExpectedStatus(e.target.value)}
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Success/Error Messages */}
      {submitSuccess && (
        <Alert className="border-teal-500 text-teal-700 dark:text-teal-300 dark:border-teal-400 animate-in slide-in-from-top-2 duration-300">
          <AlertDescription>
            Task initiated successfully! The task has been updated with your current settings.
          </AlertDescription>
        </Alert>
      )}

      {submitError && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            {submitError}
          </AlertDescription>
        </Alert>
      )}

      {/* Warning Alert */}
      {showWarning && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Please enter at least a task name and instruction.
          </AlertDescription>
        </Alert>
      )}

      {/* Action Buttons */}
      <div className={`grid grid-cols-5 gap-4 w-full transition-all duration-500 ${isSubmitting ? 'border-2 border-teal-500 rounded-lg p-2 shadow-lg shadow-teal-500/20' : ''}`}>
        <Button
          variant="outline"
          size="default"
          disabled={!isSubmitting}
          className={`flex items-center gap-2 h-12 ${isSubmitting
            ? 'bg-red-50 border-red-200 text-red-700 hover:bg-red-100 dark:bg-red-950 dark:border-red-800 dark:text-red-300 dark:hover:bg-red-900'
            : 'bg-muted/50 border-muted-foreground/20 text-muted-foreground'
            }`}
        >
          <Square className="w-4 h-4" />
          Stop
        </Button>
        <Button
          variant="outline"
          size="default"
          disabled={!isSubmitting}
          className={`flex items-center gap-2 h-12 ${isSubmitting
            ? 'bg-yellow-50 border-yellow-200 text-yellow-700 hover:bg-yellow-100 dark:bg-yellow-950 dark:border-yellow-800 dark:text-yellow-300 dark:hover:bg-yellow-900'
            : 'bg-muted/50 border-muted-foreground/20 text-muted-foreground'
            }`}
        >
          <Pause className="w-4 h-4" />
          Pause
        </Button>
        <Button
          variant="outline"
          size="default"
          disabled={!apiResponse}
          onClick={handleClear}
          className={`flex items-center gap-2 h-12 ${apiResponse
            ? 'bg-muted/50 border-muted-foreground/20 text-muted-foreground hover:bg-muted'
            : 'bg-muted/50 border-muted-foreground/20 text-muted-foreground'
            }`}
        >
          <Eraser className="w-4 h-4" />
          Clear
        </Button>
        <Button variant="outline" size="default" className="flex items-center gap-2 bg-muted/50 border-muted-foreground/20 text-muted-foreground hover:bg-muted h-12">
          <FileText className="w-4 h-4" />
          Create Script
        </Button>
        <Button
          onClick={handleSubmitTask}
          size="default"
          disabled={isSubmitting}
          className="flex items-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground h-12"
        >
          <Send className="w-4 h-4" />
          {isSubmitting ? 'Submitting...' : 'Submit Task'}
        </Button>
      </div>

      {/* Task Outputs */}
      <div className={`transition-all duration-500 ${isSubmitting ? 'border-2 border-teal-500 rounded-lg p-2 shadow-lg shadow-teal-500/20' : ''}`}>
        <Card>
          <CardHeader>
            <CardTitle>Task Outputs</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* API Response JSON */}
            {apiResponse && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  <Label>API Response JSON</Label>
                </div>
                <div className="bg-muted/20 rounded border p-4 max-h-96 overflow-auto">
                  <pre
                    className="text-sm text-muted-foreground whitespace-pre-wrap font-mono"
                    dangerouslySetInnerHTML={{ __html: formatJSON(apiResponse) }}
                  />
                </div>
              </div>
            )}

            {/* Agent History JSON */}
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4" />
                <Label>Agent History JSON</Label>
              </div>
              <div className="h-32 bg-muted/20 rounded border flex items-center justify-center">
                <p className="text-muted-foreground">No history available</p>
              </div>
            </div>

            {/* Task Recording GIF */}
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4" />
                <Label>Task Recording GIF</Label>
              </div>
              {resultLoading ? (
                <div className="h-32 bg-muted/20 rounded border flex items-center justify-center">
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  <p className="text-muted-foreground">Loading recording...</p>
                </div>
              ) : taskResult?.result_gif ? (
                <div className="bg-muted/20 rounded border p-4">
                  <img
                    src={taskResult.result_gif}
                    alt="Task Recording"
                    className="w-full h-auto rounded"
                    onError={(e) => {
                      const target = e.currentTarget as HTMLImageElement;
                      const nextDiv = target.nextElementSibling as HTMLDivElement;
                      target.style.display = 'none';
                      if (nextDiv) {
                        nextDiv.style.display = 'flex';
                      }
                    }}
                  />
                  <div className="h-32 bg-muted/20 rounded border items-center justify-center hidden">
                    <p className="text-muted-foreground">Failed to load recording</p>
                  </div>
                </div>
              ) : (
                <div className="h-32 bg-muted/20 rounded border flex items-center justify-center">
                  <p className="text-muted-foreground">
                    {task?.status === 'completed' ? 'No recording available' : 'Recording will appear when task is completed'}
                  </p>
                </div>
              )}
            </div>

            {/* Download Script */}
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Download className="w-4 h-4" />
                <Label>Download Script</Label>
              </div>
              {taskResult?.result_json_url ? (
                <button
                  onClick={handleDownloadScript}
                  className="flex items-center justify-between p-3 bg-muted/20 rounded border hover:bg-muted/30 transition-colors cursor-pointer w-full text-left"
                >
                  <span className="text-sm">task_{taskId}_script.py</span>
                  <span className="text-xs text-primary">Download ↓</span>
                </button>
              ) : (
                <div className="flex items-center justify-between p-3 bg-muted/20 rounded border">
                  <span className="text-sm text-muted-foreground">
                    {task?.status === 'completed' ? 'No script available' : 'Script will be available when task is completed'}
                  </span>
                  <span className="text-xs text-muted-foreground">—</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}; 