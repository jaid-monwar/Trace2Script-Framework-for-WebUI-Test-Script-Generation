import React from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const SettingsDialog = ({ open, onOpenChange }: SettingsDialogProps) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader className="flex flex-row items-center justify-between">
          <DialogTitle className="flex items-center gap-2">
            <span>⚙️</span>
            Settings
            <span className="text-sm text-muted-foreground">http://localhost:7788/</span>
          </DialogTitle>
          <Button variant="ghost" size="sm" onClick={() => onOpenChange(false)}>
            <X className="h-4 w-4" />
          </Button>
        </DialogHeader>
        
        <div className="space-y-6 py-4">
          {/* Display Theme */}
          <div className="space-y-3">
            <Label className="text-base font-medium">Display Theme</Label>
            <RadioGroup defaultValue="dark" className="flex gap-4">
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="light" id="light" />
                <Label htmlFor="light">☀️ Light</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="dark" id="dark" />
                <Label htmlFor="dark">🌙 Dark</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="system" id="system" />
                <Label htmlFor="system">🖥️ System</Label>
              </div>
            </RadioGroup>
          </div>

          {/* Language */}
          <div className="space-y-3">
            <Label className="text-base font-medium">Language</Label>
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

          {/* Progressive Web App */}
          <div className="space-y-3">
            <Label className="text-base font-medium">Progressive Web App</Label>
            <p className="text-sm text-muted-foreground">
              Progressive Web App is not enabled for this app. To enable it, start your Gradio app with launch(pwa=True).
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};