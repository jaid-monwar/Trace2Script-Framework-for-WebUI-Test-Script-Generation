import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Globe, Settings, Play, LogOut, ArrowLeft } from "lucide-react";
import { AgentSettings } from "@/components/AgentSettings";
import { BrowserSettings } from "@/components/BrowserSettings";
import { RunAgent } from "@/components/RunAgent";
import { ApiDocumentation } from "@/components/ApiDocumentation";
import TaskHeader from "@/components/TaskHeader";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/contexts/AuthContext";
import { useTask } from "@/contexts/TaskContext";
import { useSettings } from "@/contexts/SettingsContext";
import { getTask, TaskRead } from "@/utils/tasks-api";

const TaskDetail = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const { logout, user } = useAuth();
  const { selectedTaskId, setSelectedTaskId } = useTask();
  const { updateAgentSettings, updateBrowserSettings } = useSettings();
  const [taskData, setTaskData] = useState<TaskRead | null>(null);

  useEffect(() => {
    if (taskId) {
      setSelectedTaskId(parseInt(taskId));
      loadTaskSettings(parseInt(taskId));
    }
  }, [taskId, setSelectedTaskId]);

  const loadTaskSettings = async (taskId: number) => {
    try {
      const result = await getTask(taskId);
      if (!('error' in result)) {
        const task = result as TaskRead;

        setTaskData(task);

        updateAgentSettings({
          llmProvider: task.llm_provider || "openai",
          llmModel: task.llm_model || "gpt-4o",
          temperature: task.temperature || 0.6,
          ollamaContextLength: task.context_length || 16000,
          baseUrl: task.base_url || "",
          apiKey: task.api_key || "",
        });

        updateBrowserSettings({
          headlessMode: task.browser_headless_mode ?? true,
          disableSecurity: task.disable_security ?? true,
          windowWidth: task.window_width || 1280,
          windowHeight: task.window_height || 720,
        });
      }
    } catch (error) {
      console.error("Failed to load task settings:", error);
    }
  };

  const handleLogout = () => {
    logout();
  };

  const handleBackToTasks = () => {
    setSelectedTaskId(null);
    navigate("/");
  };



  if (!selectedTaskId) {
    return (
      <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
        <div className="text-center">
          <p className="text-muted-foreground">Loading task...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="container mx-auto p-6" style={{ width: '70vw', maxWidth: '70%', marginLeft: 'auto', marginRight: 'auto', paddingTop: '10px' }}>
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-2">
            <h1 className="text-2xl font-bold">🌐 Automated Test Script Generator</h1>
          </div>
          <p className="text-muted-foreground">Generate test scripts for your web applications</p>

          <div className="absolute top-6 left-6">
            <Button
              variant="outline"
              size="sm"
              onClick={handleBackToTasks}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Tasks</span>
            </Button>
          </div>

          <div className="absolute top-6 right-6 flex items-center gap-3">
            {user && (
              <span className="text-sm text-muted-foreground">
                Welcome, {user.username}
              </span>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={handleLogout}
              className="flex items-center gap-2"
            >
              <LogOut className="h-4 w-4" />
              <span>Logout</span>
            </Button>
          </div>
        </div>

        {taskData && (
          <TaskHeader
            taskName={taskData.task_name}
            status={taskData.status}
            createdAt={taskData.created_at}
            initiatedAt={taskData.initiated_at}
          />
        )}

        <Tabs defaultValue="agent-settings" className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-6">
            <TabsTrigger value="agent-settings" className="flex items-center gap-2">
              <Settings className="w-4 h-4" />
              Agent Settings
            </TabsTrigger>
            <TabsTrigger value="browser-settings" className="flex items-center gap-2">
              <Globe className="w-4 h-4" />
              Browser Settings
            </TabsTrigger>
            <TabsTrigger value="run-agent" className="flex items-center gap-2">
              <Play className="w-4 h-4" />
              Run Agent
            </TabsTrigger>
          </TabsList>

          <TabsContent value="agent-settings">
            <AgentSettings />
          </TabsContent>

          <TabsContent value="browser-settings">
            <BrowserSettings />
          </TabsContent>

          <TabsContent value="run-agent">
            <RunAgent setTaskData={setTaskData} />
          </TabsContent>
        </Tabs>

        <div className="mt-8">
          <div className="flex items-center justify-center gap-4 text-sm text-muted-foreground">
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="ghost" className="flex items-center gap-2 text-warning">
                  Use via API
                  <span>🚀</span>
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-[67vw] max-w-none sm:max-w-none flex flex-col">
                <SheetHeader className="flex-shrink-0">
                  <SheetTitle className="flex items-center gap-2">
                    <span>🚀</span>
                    API Documentation
                  </SheetTitle>
                </SheetHeader>
                <div className="flex-1 overflow-hidden">
                  <ApiDocumentation />
                </div>
              </SheetContent>
            </Sheet>

            <Sheet>
              <SheetTrigger asChild>
                <Button variant="ghost" size="sm" className="flex items-center gap-1">
                  Settings
                  <Settings className="w-4 h-4" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-[67vw] max-w-none sm:max-w-none">
                <SheetHeader>
                  <SheetTitle className="flex items-center gap-2">
                    <Settings className="w-4 h-4" />
                    Settings
                  </SheetTitle>
                </SheetHeader>
                <div className="mt-6 space-y-6">
                  <div className="space-y-2">
                    <Label className="text-base font-semibold">Display Theme</Label>
                    <div className="flex gap-2">
                      <Button variant="ghost" size="sm" className="flex items-center gap-2">
                        ☀️ Light
                      </Button>
                      <Button variant="default" size="sm" className="flex items-center gap-2">
                        🌙 Dark
                      </Button>
                      <Button variant="ghost" size="sm" className="flex items-center gap-2">
                        💻 System
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-base font-semibold">Language</Label>
                    <Select defaultValue="english">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="english">English</SelectItem>
                        <SelectItem value="spanish">Spanish</SelectItem>
                        <SelectItem value="french">French</SelectItem>
                        <SelectItem value="german">German</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-base font-semibold">Progressive Web App</Label>
                    <p className="text-sm text-muted-foreground">
                      Progressive Web App is not enabled for this app. To enable it, start your Gradio app with launch(pwa=True).
                    </p>
                  </div>
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaskDetail; 