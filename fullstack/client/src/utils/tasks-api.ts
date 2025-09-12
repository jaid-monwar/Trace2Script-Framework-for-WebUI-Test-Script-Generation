import axios from 'axios';
import { API_BASE_URL, getAuthHeaders } from './api-config';

export interface TaskSummary {
  id: number;
  task_name: string;
  status: string;
}

export interface TaskRead {
  task_name: string;
  status: string;
  llm_provider: string;
  llm_model: string;
  temperature: number;
  context_length: number;
  base_url: string;
  api_key: string;
  browser_headless_mode: boolean;
  disable_security: boolean;
  window_width: number;
  window_height: number;
  instruction: string;
  description: string;
  search_input_input: string;
  search_input_action: string;
  expected_outcome: string;
  expected_status: string;
  id: number;
  user_id: number;
  created_at: string;
  initiated_at: string;
}



export interface AgentSettings {
  llm_provider: string;
  llm_model: string;
  temperature: number;
  context_length: number;
  base_url: string;
  api_key: string;
}

export interface BrowserSettings {
  browser_headless_mode: boolean;
  disable_security: boolean;
  window_width: number;
  window_height: number;
}

export interface TaskInitiate {
  instruction: string;
  description: string;
  search_input_input: string;
  search_input_action: string;
  expected_outcome: string;
  expected_status: string;
  api_key?: string;
}

export interface TaskResult {
  result_gif: string;
  result_json_url: string;
  task_id: number;
}

export const getTasks = async (): Promise<TaskSummary[] | { error: string }> => {
  try {
    const res = await axios.get(`${API_BASE_URL}/tasks`, {
      headers: getAuthHeaders(),
    });

    if (res.status === 200) {
      return res.data;
    }

  } catch (err) {
    if (err.response) {
      const errorMessage = err.response.data?.detail || err.response.data?.message || "Failed to fetch tasks";
      return { error: errorMessage };
    } else if (err.request) {
      return { error: "No response from server. Check your connection." };
    } else {
      return { error: "An unexpected error occurred." };
    }
  }
};

export const createTask = async (taskName: string): Promise<TaskRead | { error: string }> => {
  try {
    const res = await axios.post(`${API_BASE_URL}/tasks`, { task_name: taskName }, {
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
    });

    if (res.status === 200 || res.status === 201) {
      return res.data;
    }

  } catch (err) {
    if (err.response) {
      const errorMessage = err.response.data?.detail || err.response.data?.message || "Failed to create task";
      return { error: errorMessage };
    } else if (err.request) {
      return { error: "No response from server. Check your connection." };
    } else {
      return { error: "An unexpected error occurred." };
    }
  }
};

export const getTask = async (taskId: number): Promise<TaskRead | { error: string }> => {
  try {
    const res = await axios.get(`${API_BASE_URL}/tasks/${taskId}`, {
      headers: getAuthHeaders(),
    });

    if (res.status === 200) {
      return res.data;
    }

  } catch (err) {
    if (err.response) {
      const errorMessage = err.response.data?.detail || err.response.data?.message || "Failed to fetch task";
      return { error: errorMessage };
    } else if (err.request) {
      return { error: "No response from server. Check your connection." };
    } else {
      return { error: "An unexpected error occurred." };
    }
  }
};

export const deleteTask = async (taskId: number): Promise<string | { error: string }> => {
  try {
    const res = await axios.delete(`${API_BASE_URL}/tasks/${taskId}`, {
      headers: getAuthHeaders(),
    });

    if (res.status === 200) {
      return res.data;
    }

  } catch (err) {
    if (err.response) {
      const errorMessage = err.response.data?.detail || err.response.data?.message || "Failed to delete task";
      return { error: errorMessage };
    } else if (err.request) {
      return { error: "No response from server. Check your connection." };
    } else {
      return { error: "An unexpected error occurred." };
    }
  }
};

export const updateAgentSettings = async (taskId: number, agentSettings: AgentSettings): Promise<TaskRead | { error: string }> => {
  try {
    const res = await axios.patch(`${API_BASE_URL}/tasks/${taskId}/agent-settings`, agentSettings, {
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
    });

    if (res.status === 200) {
      return res.data;
    }

  } catch (err) {
    if (err.response) {
      const errorMessage = err.response.data?.detail || err.response.data?.message || "Failed to update agent settings";
      return { error: errorMessage };
    } else if (err.request) {
      return { error: "No response from server. Check your connection." };
    } else {
      return { error: "An unexpected error occurred." };
    }
  }
};

export const updateBrowserSettings = async (taskId: number, browserSettings: BrowserSettings): Promise<TaskRead | { error: string }> => {
  try {
    const res = await axios.patch(`${API_BASE_URL}/tasks/${taskId}/browser-settings`, browserSettings, {
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
    });

    if (res.status === 200) {
      return res.data;
    }

  } catch (err) {
    if (err.response) {
      const errorMessage = err.response.data?.detail || err.response.data?.message || "Failed to update browser settings";
      return { error: errorMessage };
    } else if (err.request) {
      return { error: "No response from server. Check your connection." };
    } else {
      return { error: "An unexpected error occurred." };
    }
  }
};

export const initiateTask = async (taskId: number, taskData: TaskInitiate): Promise<TaskRead | { error: string }> => {
  try {
    const res = await axios.patch(`${API_BASE_URL}/tasks/${taskId}/initiate`, taskData, {
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
    });

    if (res.status === 200) {
      return res.data;
    }

  } catch (err) {
    if (err.response) {
      const errorMessage = err.response.data?.detail || err.response.data?.message || "Failed to initiate task";
      return { error: errorMessage };
    } else if (err.request) {
      return { error: "No response from server. Check your connection." };
    } else {
      return { error: "An unexpected error occurred." };
    }
  }
};

export const getTaskResult = async (taskId: number): Promise<TaskResult | { error: string }> => {
  try {
    const res = await axios.get(`${API_BASE_URL}/results/${taskId}`, {
      headers: getAuthHeaders(),
    });

    if (res.status === 200) {
      return res.data;
    }

  } catch (err) {
    if (err.response) {
      const errorMessage = err.response.data?.detail || err.response.data?.message || "Failed to fetch task result";
      return { error: errorMessage };
    } else if (err.request) {
      return { error: "No response from server. Check your connection." };
    } else {
      return { error: "An unexpected error occurred." };
    }
  }
};
