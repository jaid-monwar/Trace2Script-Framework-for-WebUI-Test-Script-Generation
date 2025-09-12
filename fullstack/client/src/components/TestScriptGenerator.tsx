
import React, { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Globe, Settings, Play, LogOut } from "lucide-react";
import { AgentSettings } from "./AgentSettings";
import { BrowserSettings } from "./BrowserSettings";
import { RunAgent } from "./RunAgent";
import { ApiDocumentation } from "./ApiDocumentation";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/contexts/AuthContext";

export const TestScriptGenerator = () => {
  const { logout, user } = useAuth();

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="container mx-auto p-6" style={{ width: '70vw', maxWidth: '70%', marginLeft: 'auto', marginRight: 'auto', paddingTop: '10px' }}>
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-2">
            <h1 className="text-2xl font-bold">🌐 Automated Test Script Generator</h1>
          </div>
          <p className="text-muted-foreground">Generate test scripts for your web applications</p>
          
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
            <RunAgent />
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
