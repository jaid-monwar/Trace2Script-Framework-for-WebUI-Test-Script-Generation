import React from "react";
import { LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import Tasks from "./Tasks";

const Index = () => {
  const { logout, user } = useAuth();

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="container mx-auto p-6" style={{ width: '70vw', maxWidth: '70%', marginLeft: 'auto', marginRight: 'auto', paddingTop: '10px' }}>
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-2">
            <h1 className="text-2xl font-bold">🌐 Automated Test Script Generator</h1>
          </div>
          <p className="text-muted-foreground">Generate test scripts for your web applications</p>
          
          {/* Logout Button */}
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

        {/* Tasks Content */}
        <Tasks />
      </div>
    </div>
  );
};

export default Index;
