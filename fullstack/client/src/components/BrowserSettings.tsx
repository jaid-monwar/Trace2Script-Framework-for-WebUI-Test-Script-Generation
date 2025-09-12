import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertTriangle, Loader2, Save } from "lucide-react";
import { useSettings } from "@/contexts/SettingsContext";
import { useTask } from "@/contexts/TaskContext";
import { updateBrowserSettings as updateBrowserSettingsAPI, BrowserSettings as BrowserSettingsType } from "@/utils/tasks-api";

export const BrowserSettings = () => {
  const { settings, updateBrowserSettings } = useSettings();
  const { selectedTaskId } = useTask();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleSaveSettings = async () => {
    if (!selectedTaskId) {
      setError("No task selected. Please select a task first.");
      return;
    }

    setSaving(true);
    setError("");
    setSuccess(false);

    try {
      const browserSettings: BrowserSettingsType = {
        browser_headless_mode: settings.browser.headlessMode,
        disable_security: settings.browser.disableSecurity,
        window_width: settings.browser.windowWidth,
        window_height: settings.browser.windowHeight,
      };

      const result = await updateBrowserSettingsAPI(selectedTaskId, browserSettings);

      if ('error' in result) {
        setError(result.error);
      } else {
        setSuccess(true);
        setTimeout(() => setSuccess(false), 3000);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to save browser settings");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Browser Settings
          {selectedTaskId && (
            <Button 
              onClick={handleSaveSettings}
              disabled={saving}
              size="sm"
              className="flex items-center gap-2"
            >
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  Save Settings
                </>
              )}
            </Button>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        {/* Success/Error Messages */}
        {success && (
          <Alert className="mb-4 border-teal-500 text-teal-700 dark:text-teal-300 dark:border-teal-400">
            <AlertDescription>
              Browser settings saved successfully!
            </AlertDescription>
          </Alert>
        )}

        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Keep Browser Open between Tasks</Label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox 
                id="keep-browser-open" 
                checked={settings.browser.keepBrowserOpen}
                onCheckedChange={(checked) => updateBrowserSettings({ keepBrowserOpen: checked === true })}
              />
              <Label htmlFor="keep-browser-open" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                Keep Browser Open
              </Label>
            </div>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Run browser without GUI</Label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox 
                id="headless-mode" 
                checked={settings.browser.headlessMode}
                onCheckedChange={(checked) => updateBrowserSettings({ headlessMode: checked === true })}
              />
              <Label htmlFor="headless-mode" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                Headless Mode
              </Label>
            </div>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Disable browser security</Label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox 
                id="disable-security" 
                checked={settings.browser.disableSecurity}
                onCheckedChange={(checked) => updateBrowserSettings({ disableSecurity: checked === true })}
              />
              <Label htmlFor="disable-security" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                Disable Security
              </Label>
            </div>
          </div>
        </div> */}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
          {/* Window Width */}
          <div className="space-y-2">
            <Label htmlFor="window-width">Window Width</Label>
            <p className="text-sm text-muted-foreground">Browser window width</p>
            <Input 
              id="window-width"
              type="number"
              value={settings.browser.windowWidth}
              onChange={(e) => updateBrowserSettings({ windowWidth: parseInt(e.target.value) || 1280 })}
              className="w-full"
            />
          </div>

          {/* Window Height */}
          <div className="space-y-2">
            <Label htmlFor="window-height">Window Height</Label>
            <p className="text-sm text-muted-foreground">Browser window height</p>
            <Input 
              id="window-height"
              type="number"
              value={settings.browser.windowHeight}
              onChange={(e) => updateBrowserSettings({ windowHeight: parseInt(e.target.value) || 720 })}
              className="w-full"
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
