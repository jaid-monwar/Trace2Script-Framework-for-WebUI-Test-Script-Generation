import React from "react";
import { Calendar, Play } from "lucide-react";

interface TaskHeaderProps {
    taskName: string;
    status: string;
    createdAt: string;
    initiatedAt: string;
}

const TaskHeader: React.FC<TaskHeaderProps> = ({ taskName, status, createdAt, initiatedAt }) => {
    const formatDateTime = (isoString: string): string => {
        if (!isoString) return "Not set";

        try {
            const utc = new Date(isoString);
            var offset = utc.getTimezoneOffset();
            var date = new Date(utc.getTime() + offset * 60000);
            return date.toLocaleString(undefined, {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                timeZoneName: 'short'
            });
        } catch (error) {
            return "Invalid date";
        }
    };

    const getStatusConfig = () => {
        const statusConfigs = {
            running: {
                color: "bg-blue-500",
                text: "Running"
            },
            completed: {
                color: "bg-green-500",
                text: "Completed"
            },
            failed: {
                color: "bg-red-500",
                text: "Failed"
            }
        };

        return statusConfigs[status as keyof typeof statusConfigs] || null;
    };

    const statusConfig = getStatusConfig();

    return (
        <div className="bg-card border rounded-lg p-6 mb-6">
            <div className="flex flex-col space-y-4">
                {/* Task Name and Status */}
                <div className="flex items-center gap-3">
                    <h2 className="text-2xl font-bold text-foreground">{taskName}</h2>
                    {statusConfig && (
                        <div className="flex items-center gap-2">
                            <div className={`w-3 h-3 rounded-full ${statusConfig.color}`}></div>
                            <span className="text-sm font-medium text-muted-foreground">{statusConfig.text}</span>
                        </div>
                    )}
                </div>

                {/* Timestamps */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div className="flex items-center gap-2 text-muted-foreground">
                        <Calendar className="h-4 w-4" />
                        <span className="font-medium">Created:</span>
                        <span>{formatDateTime(createdAt)}</span>
                    </div>

                    <div className="flex items-center gap-2 text-muted-foreground">
                        <Play className="h-4 w-4" />
                        <span className="font-medium">Initiated:</span>
                        <span>{formatDateTime(initiatedAt)}</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TaskHeader;