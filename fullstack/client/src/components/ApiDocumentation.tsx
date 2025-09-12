
import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Copy } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";

export const ApiDocumentation = () => {
  const [selectedLanguage, setSelectedLanguage] = useState<"python" | "javascript" | "bash">("python");
  
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const apiEndpoints = [
    {
      name: "/lambda",
      description: "LLM Provider selection endpoint",
      parameter: {
        name: "x",
        type: "Literal['anthropic', 'openai', 'deepseek', 'google', 'ollama', 'azure_openai', 'mistral', 'alibaba', 'moonshot', 'unbound', 'siliconflow', 'ibm']",
        default: "openai",
        description: "The input value that is provided in the \"LLM Provider\" Dropdown component."
      },
      returns: {
        type: "float",
        description: "The output value that appears in the \"Ollama Context Length\" Slider component."
      },
      python: `from gradio_client import Client

client = Client("http://localhost:7788/")
result = client.predict(
    x="openai",
    api_name="/lambda"
)
print(result)`,
      javascript: `import { Client } from "@gradio/client";

const client = await Client.connect("http://localhost:7788/");
const result = await client.predict("/lambda", { 		
		x: "anthropic", 
});

console.log(result.data);`,
      bash: `curl -X POST http://localhost:7788/gradio_api/call/lambda -s -H "Content-Type: application/json" -d '{
  "data": [
							"anthropic"
]}' \\
  | awk -F'"' '{ print $4}'  \\
  | read EVENT_ID; curl -N http://localhost:7788/gradio_api/call/lambda/$EVENT_ID`
    },
    {
      name: "/lambda_1",
      description: "LLM Model Name selection endpoint",
      parameter: {
        name: "provider",
        type: "Literal['anthropic', 'openai', 'deepseek', 'google', 'ollama', 'azure_openai', 'mistral', 'alibaba', 'moonshot', 'unbound', 'siliconflow', 'ibm']",
        default: "openai",
        description: "The input value that is provided in the \"LLM Provider\" Dropdown component."
      },
      returns: {
        type: "Literal['gpt-4o', 'gpt-4', 'gpt-3.5-turbo', 'o3-mini']",
        description: "The output value that appears in the \"LLM Model Name\" Dropdown component."
      },
      python: `from gradio_client import Client

client = Client("http://localhost:7788/")
result = client.predict(
		provider="openai",
		api_name="/lambda_1"
)
print(result)`,
      javascript: `import { Client } from "@gradio/client";

const client = await Client.connect("http://localhost:7788/");
const result = await client.predict("/lambda_1", { 		
		provider: "anthropic", 
});

console.log(result.data);`,
      bash: `curl -X POST http://localhost:7788/gradio_api/call/lambda_1 -s -H "Content-Type: application/json" -d '{
  "data": [
							"anthropic"
]}' \\
  | awk -F'"' '{ print $4}'  \\
  | read EVENT_ID; curl -N http://localhost:7788/gradio_api/call/lambda_1/$EVENT_ID`
    },
    {
      name: "/close_wrapper",
      description: "Close wrapper endpoint",
      parameter: {
        name: "none",
        type: "none",
        default: "none",
        description: "No parameters required."
      },
      returns: {
        type: "none",
        description: "No return value specified."
      },
      python: `from gradio_client import Client

client = Client("http://localhost:7788/")
result = client.predict(
		api_name="/close_wrapper"
)
print(result)`,
      javascript: `import { Client } from "@gradio/client";

const client = await Client.connect("http://localhost:7788/");
const result = await client.predict("/close_wrapper", { 
});

console.log(result.data);`,
      bash: `curl -X POST http://localhost:7788/gradio_api/call/close_wrapper -s -H "Content-Type: application/json" -d '{
  "data": [
]}' \\
  | awk -F'"' '{ print $4}'  \\
  | read EVENT_ID; curl -N http://localhost:7788/gradio_api/call/close_wrapper/$EVENT_ID`
    },
    {
      name: "/close_wrapper_1",
      description: "Close wrapper 1 endpoint",
      parameter: {
        name: "none",
        type: "none",
        default: "none",
        description: "No parameters required."
      },
      returns: {
        type: "none",
        description: "No return value specified."
      },
      python: `from gradio_client import Client

client = Client("http://localhost:7788/")
result = client.predict(
		api_name="/close_wrapper_1"
)
print(result)`,
      javascript: `import { Client } from "@gradio/client";

const client = await Client.connect("http://localhost:7788/");
const result = await client.predict("/close_wrapper_1", { 
});

console.log(result.data);`,
      bash: `curl -X POST http://localhost:7788/gradio_api/call/close_wrapper_1 -s -H "Content-Type: application/json" -d '{
  "data": [
]}' \\
  | awk -F'"' '{ print $4}'  \\
  | read EVENT_ID; curl -N http://localhost:7788/gradio_api/call/close_wrapper_1/$EVENT_ID`
    },
    {
      name: "/close_wrapper_2",
      description: "Close wrapper 2 endpoint",
      parameter: {
        name: "none",
        type: "none",
        default: "none",
        description: "No parameters required."
      },
      returns: {
        type: "none",
        description: "No return value specified."
      },
      python: `from gradio_client import Client

client = Client("http://localhost:7788/")
result = client.predict(
		api_name="/close_wrapper_2"
)
print(result)`,
      javascript: `import { Client } from "@gradio/client";

const client = await Client.connect("http://localhost:7788/");
const result = await client.predict("/close_wrapper_2", { 
});

console.log(result.data);`,
      bash: `curl -X POST http://localhost:7788/gradio_api/call/close_wrapper_2 -s -H "Content-Type: application/json" -d '{
  "data": [
]}' \\
  | awk -F'"' '{ print $4}'  \\
  | read EVENT_ID; curl -N http://localhost:7788/gradio_api/call/close_wrapper_2/$EVENT_ID`
    },
    {
      name: "/submit_wrapper",
      description: "Submit task for execution",
      parameter: {
        name: "25 parameters",
        type: "complex",
        default: "various",
        description: "Accepts 25 parameters including components_dict, param_1 through param_29 for various UI components."
      },
      returns: {
        type: "tuple of 13 elements",
        description: "Returns a tuple with 13 elements including chatbot updates, file outputs, and browser view."
      },
      python: `from gradio_client import Client, handle_file

client = Client("http://localhost:7788/")
result = client.predict(
		components_dict="openai",
		param_1="gpt-4o",
		param_2=0.6,
		param_3=False,
		param_4=16000,
		param_5="",
		param_6="",
		param_7=True,
		param_8=False,
		param_9=True,
		param_10=1280,
		param_11=720,
		param_12=[],
		param_13="Hello!!",
		param_14="Hello!!",
		param_15="Hello!!",
		param_16="Hello!!",
		param_17="Hello!!",
		param_18="Hello!!",
		param_19="Hello!!",
		param_20="Hello!!",
		param_26="<div style='width:100%; height:50vh; display:flex; justify-content:center; align-items:center; border:1px solid #ccc; background-color:#f0f0f0;'><p>Browser View (Requires Headless=True)</p></div>",
		param_27=handle_file('https://github.com/gradio-app/gradio/raw/main/test/test_files/sample_file.pdf'),
		param_28=handle_file('https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png'),
		param_29=handle_file('https://github.com/gradio-app/gradio/raw/main/test/test_files/sample_file.pdf'),
		api_name="/submit_wrapper"
)
print(result)`,
      javascript: `import { Client } from "@gradio/client";

const response_0 = await fetch("https://github.com/gradio-app/gradio/raw/main/test/test_files/sample_file.pdf");
const exampleFile = await response_0.blob();
						
const response_1 = await fetch("https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png");
const exampleImage = await response_1.blob();
						
const response_2 = await fetch("https://github.com/gradio-app/gradio/raw/main/test/test_files/sample_file.pdf");
const exampleFile = await response_2.blob();
						
const client = await Client.connect("http://localhost:7788/");
const result = await client.predict("/submit_wrapper", { 		
		components_dict: "anthropic", 		
		param_1: "gpt-4o", 		
		param_2: 0, 		
		param_3: true, 		
		param_4: 256, 		
		param_5: "Hello!!", 		
		param_6: "Hello!!", 		
		param_7: true, 		
		param_8: true, 		
		param_9: true, 		
		param_10: 3, 		
		param_11: 3, 		
		param_12: [{"role":"user","metadata":None,"content":"Hello!","options":None},{"role":"assistant","metadata":None,"content":"How can I help you?","options":None}], 		
		param_13: "Hello!!", 		
		param_14: "Hello!!", 		
		param_15: "Hello!!", 		
		param_16: "Hello!!", 		
		param_17: "Hello!!", 		
		param_18: "Hello!!", 		
		param_19: "Hello!!", 		
		param_20: "Hello!!", 		
		param_26: "<p>Hello</p>", 
		param_27: exampleFile, 
		param_28: exampleImage, 
		param_29: exampleFile, 
});

console.log(result.data);`,
      bash: `curl -X POST http://localhost:7788/gradio_api/call/submit_wrapper -s -H "Content-Type: application/json" -d '{
  "data": [
							"anthropic",
							"gpt-4o",
							0,
							true,
							256,
							"Hello!!",
							"Hello!!",
							true,
							true,
							true,
							3,
							3,
							[{"role":"user","metadata":None,"content":"Hello!","options":None},{"role":"assistant","metadata":None,"content":"How can I help you?","options":None}],
							"Hello!!",
							"Hello!!",
							"Hello!!",
							"Hello!!",
							"Hello!!",
							"Hello!!",
							"Hello!!",
							"Hello!!",
							"<p>Hello</p>",
							{"path":"https://github.com/gradio-app/gradio/raw/main/test/test_files/sample_file.pdf","meta":{"_type":"gradio.FileData"}},
							{"path":"https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png","meta":{"_type":"gradio.FileData"}},
							{"path":"https://github.com/gradio-app/gradio/raw/main/test/test_files/sample_file.pdf","meta":{"_type":"gradio.FileData"}}
]}' \\
  | awk -F'"' '{ print $4}'  \\
  | read EVENT_ID; curl -N http://localhost:7788/gradio_api/call/submit_wrapper/$EVENT_ID`
    },
    {
      name: "/stop_wrapper",
      description: "Stop task execution",
      parameter: {
        name: "none",
        type: "none",
        default: "none",
        description: "No parameters required."
      },
      returns: {
        type: "tuple of 13 elements",
        description: "Returns a tuple with 13 elements including chatbot updates, file outputs, and browser view."
      },
      python: `from gradio_client import Client

client = Client("http://localhost:7788/")
result = client.predict(
		api_name="/stop_wrapper"
)
print(result)`,
      javascript: `import { Client } from "@gradio/client";

const client = await Client.connect("http://localhost:7788/");
const result = await client.predict("/stop_wrapper", { 
});

console.log(result.data);`,
      bash: `curl -X POST http://localhost:7788/gradio_api/call/stop_wrapper -s -H "Content-Type: application/json" -d '{
  "data": [
]}' \\
  | awk -F'"' '{ print $4}'  \\
  | read EVENT_ID; curl -N http://localhost:7788/gradio_api/call/stop_wrapper/$EVENT_ID`
    },
    {
      name: "/pause_resume_wrapper",
      description: "Pause or resume task execution",
      parameter: {
        name: "none",
        type: "none",
        default: "none",
        description: "No parameters required."
      },
      returns: {
        type: "tuple of 13 elements",
        description: "Returns a tuple with 13 elements including chatbot updates, file outputs, and browser view."
      },
      python: `from gradio_client import Client

client = Client("http://localhost:7788/")
result = client.predict(
		api_name="/pause_resume_wrapper"
)
print(result)`,
      javascript: `import { Client } from "@gradio/client";

const client = await Client.connect("http://localhost:7788/");
const result = await client.predict("/pause_resume_wrapper", { 
});

console.log(result.data);`,
      bash: `curl -X POST http://localhost:7788/gradio_api/call/pause_resume_wrapper -s -H "Content-Type: application/json" -d '{
  "data": [
]}' \\
  | awk -F'"' '{ print $4}'  \\
  | read EVENT_ID; curl -N http://localhost:7788/gradio_api/call/pause_resume_wrapper/$EVENT_ID`
    },
    {
      name: "/clear_wrapper",
      description: "Clear task history",
      parameter: {
        name: "none",
        type: "none",
        default: "none",
        description: "No parameters required."
      },
      returns: {
        type: "tuple of 13 elements",
        description: "Returns a tuple with 13 elements including chatbot updates, file outputs, and browser view."
      },
      python: `from gradio_client import Client

client = Client("http://localhost:7788/")
result = client.predict(
		api_name="/clear_wrapper"
)
print(result)`,
      javascript: `import { Client } from "@gradio/client";

const client = await Client.connect("http://localhost:7788/");
const result = await client.predict("/clear_wrapper", { 
});

console.log(result.data);`,
      bash: `curl -X POST http://localhost:7788/gradio_api/call/clear_wrapper -s -H "Content-Type: application/json" -d '{
  "data": [
]}' \\
  | awk -F'"' '{ print $4}'  \\
  | read EVENT_ID; curl -N http://localhost:7788/gradio_api/call/clear_wrapper/$EVENT_ID`
    },
    {
      name: "/create_script_wrapper",
      description: "Create test script",
      parameter: {
        name: "none",
        type: "none",
        default: "none",
        description: "No parameters required."
      },
      returns: {
        type: "tuple of 13 elements",
        description: "Returns a tuple with 13 elements including chatbot updates, file outputs, and browser view."
      },
      python: `from gradio_client import Client

client = Client("http://localhost:7788/")
result = client.predict(
		api_name="/create_script_wrapper"
)
print(result)`,
      javascript: `import { Client } from "@gradio/client";

const client = await Client.connect("http://localhost:7788/");
const result = await client.predict("/create_script_wrapper", { 
});

console.log(result.data);`,
      bash: `curl -X POST http://localhost:7788/gradio_api/call/create_script_wrapper -s -H "Content-Type: application/json" -d '{
  "data": [
]}' \\
  | awk -F'"' '{ print $4}'  \\
  | read EVENT_ID; curl -N http://localhost:7788/gradio_api/call/create_script_wrapper/$EVENT_ID`
    },
    {
      name: "/lambda_2",
      description: "Agent interaction endpoint",
      parameter: {
        name: "none",
        type: "none",
        default: "none",
        description: "No parameters required."
      },
      returns: {
        type: "list[dict]",
        description: "The output value that appears in the \"Agent Interaction\" Chatbot component."
      },
      python: `from gradio_client import Client

client = Client("http://localhost:7788/")
result = client.predict(
		api_name="/lambda_2"
)
print(result)`,
      javascript: `import { Client } from "@gradio/client";

const client = await Client.connect("http://localhost:7788/");
const result = await client.predict("/lambda_2", { 
});

console.log(result.data);`,
      bash: `curl -X POST http://localhost:7788/gradio_api/call/lambda_2 -s -H "Content-Type: application/json" -d '{
  "data": [
]}' \\
  | awk -F'"' '{ print $4}'  \\
  | read EVENT_ID; curl -N http://localhost:7788/gradio_api/call/lambda_2/$EVENT_ID`
    }
  ];

  const detailedParameters = {
    "/submit_wrapper": [
      {
        name: "components_dict",
        type: "Literal['anthropic', 'openai', 'deepseek', 'google', 'ollama', 'azure_openai', 'mistral', 'alibaba', 'moonshot', 'unbound', 'siliconflow', 'ibm']",
        default: "openai",
        description: "The input value that is provided in the \"LLM Provider\" Dropdown component."
      },
      {
        name: "param_1",
        type: "Literal['gpt-4o', 'gpt-4', 'gpt-3.5-turbo', 'o3-mini']",
        default: "gpt-4o",
        description: "The input value that is provided in the \"LLM Model Name\" Dropdown component."
      },
      {
        name: "param_2",
        type: "float",
        default: "0.6",
        description: "The input value that is provided in the \"LLM Temperature\" Slider component."
      },
      {
        name: "param_3",
        type: "bool",
        default: "False",
        description: "The input value that is provided in the \"Use Vision\" Checkbox component."
      },
      {
        name: "param_4",
        type: "float",
        default: "16000",
        description: "The input value that is provided in the \"Ollama Context Length\" Slider component."
      },
      {
        name: "param_5",
        type: "str",
        default: "",
        description: "The input value that is provided in the \"Base URL\" Textbox component."
      },
      {
        name: "param_6",
        type: "str",
        default: "",
        description: "The input value that is provided in the \"API Key\" Textbox component."
      },
      {
        name: "param_7",
        type: "bool",
        default: "True",
        description: "The input value that is provided in the \"Keep Browser Open\" Checkbox component."
      },
      {
        name: "param_8",
        type: "bool",
        default: "False",
        description: "The input value that is provided in the \"Headless Mode\" Checkbox component."
      },
      {
        name: "param_9",
        type: "bool",
        default: "True",
        description: "The input value that is provided in the \"Disable Security\" Checkbox component."
      },
      {
        name: "param_10",
        type: "float",
        default: "1280",
        description: "The input value that is provided in the \"Window Width\" Number component."
      },
      {
        name: "param_11",
        type: "float",
        default: "720",
        description: "The input value that is provided in the \"Window Height\" Number component."
      },
      {
        name: "param_12",
        type: "list[dict]",
        default: "[]",
        description: "The input value that is provided in the \"Agent Interaction\" Chatbot component. null"
      },
      {
        name: "param_13",
        type: "str",
        default: "Required",
        description: "The input value that is provided in the \"User Input\" Textbox component."
      },
      {
        name: "param_14",
        type: "str",
        default: "Required",
        description: "The input value that is provided in the \"Task Name\" Textbox component."
      },
      {
        name: "param_15",
        type: "str",
        default: "Required",
        description: "The input value that is provided in the \"Instruction\" Textbox component."
      },
      {
        name: "param_16",
        type: "str",
        default: "Required",
        description: "The input value that is provided in the \"Description\" Textbox component."
      },
      {
        name: "param_17",
        type: "str",
        default: "Required",
        description: "The input value that is provided in the \"Search Input\" Textbox component."
      },
      {
        name: "param_18",
        type: "str",
        default: "Required",
        description: "The input value that is provided in the \"Action\" Textbox component."
      },
      {
        name: "param_19",
        type: "str",
        default: "Required",
        description: "The input value that is provided in the \"Expected Outcome\" Textbox component."
      },
      {
        name: "param_20",
        type: "str",
        default: "Required",
        description: "The input value that is provided in the \"Expected Status\" Textbox component."
      },
      {
        name: "param_26",
        type: "str",
        default: "<div style='width:100%; height:50vh; display:flex; justify-content:center; align-items:center; border:1px solid #ccc; background-color:#f0f0f0;'><p>Browser View (Requires Headless=True)</p></div>",
        description: "The input value that is provided in the \"Browser Live View\" Html component."
      },
      {
        name: "param_27",
        type: "filepath",
        default: "Required",
        description: "The input value that is provided in the \"Agent History JSON\" File component. The FileData class is a subclass of the GradioModel class that represents a file object within a Gradio interface. It is used to store file data and metadata when a file is uploaded. Attributes: path: The server file path where the file is stored. url: The normalized server URL pointing to the file. size: The size of the file in bytes. orig_name: The original filename before upload. mime_type: The MIME type of the file. is_stream: Indicates whether the file is a stream. meta: Additional metadata used internally (should not be changed)."
      },
      {
        name: "param_28",
        type: "dict",
        default: "Required",
        description: "The input value that is provided in the \"Task Recording GIF\" Image component. For input, either path or url must be provided. For output, path is always provided."
      },
      {
        name: "param_29",
        type: "filepath",
        default: "Required",
        description: "The input value that is provided in the \"Download Script\" File component. The FileData class is a subclass of the GradioModel class that represents a file object within a Gradio interface. It is used to store file data and metadata when a file is uploaded. Attributes: path: The server file path where the file is stored. url: The normalized server URL pointing to the file. size: The size of the file in bytes. orig_name: The original filename before upload. mime_type: The MIME type of the file. is_stream: Indicates whether the file is a stream. meta: Additional metadata used internally (should not be changed)."
      }
    ]
  };

  const returnValues = {
    "/submit_wrapper": [
      {
        index: "[0]",
        type: "list[dict]",
        description: "The output value that appears in the \"Agent Interaction\" Chatbot component."
      },
      {
        index: "[1]",
        type: "str",
        description: "The output value that appears in the \"User Input\" Textbox component."
      },
      {
        index: "[2]",
        type: "str",
        description: "The output value that appears in the \"Task Name\" Textbox component."
      },
      {
        index: "[3]",
        type: "str",
        description: "The output value that appears in the \"Instruction\" Textbox component."
      },
      {
        index: "[4]",
        type: "str",
        description: "The output value that appears in the \"Description\" Textbox component."
      },
      {
        index: "[5]",
        type: "str",
        description: "The output value that appears in the \"Search Input\" Textbox component."
      },
      {
        index: "[6]",
        type: "str",
        description: "The output value that appears in the \"Action\" Textbox component."
      },
      {
        index: "[7]",
        type: "str",
        description: "The output value that appears in the \"Expected Outcome\" Textbox component."
      },
      {
        index: "[8]",
        type: "str",
        description: "The output value that appears in the \"Expected Status\" Textbox component."
      },
      {
        index: "[9]",
        type: "filepath",
        description: "The output value that appears in the \"Agent History JSON\" File component."
      },
      {
        index: "[10]",
        type: "dict",
        description: "The output value that appears in the \"Task Recording GIF\" Image component."
      },
      {
        index: "[11]",
        type: "str",
        description: "The output value that appears in the \"Browser Live View\" Html component."
      },
      {
        index: "[12]",
        type: "filepath",
        description: "The output value that appears in the \"Download Script\" File component."
      }
    ]
  };

  return (
    <ScrollArea className="h-full">
      <div className="space-y-6 p-6">
        <div className="flex items-center gap-2 mb-4">
            <span className="text-sm text-muted-foreground">http://localhost:7788/</span>
            <div className="ml-auto flex items-center gap-2">
            <Badge variant="destructive" className="flex items-center gap-1">
              <div className="w-2 h-2 bg-red-500 rounded-full"></div>
              API Recorder
            </Badge>
              <Badge variant="outline">{apiEndpoints.length} API endpoints</Badge>
            </div>
        </div>

          <p className="text-sm text-muted-foreground">
            Choose a language to see the code snippets for interacting with the API.
          </p>

          {/* Language Tabs */}
          <div className="flex gap-2">
            <Button
              size="sm"
              variant={selectedLanguage === "python" ? "default" : "outline"}
              onClick={() => setSelectedLanguage("python")}
              className="flex items-center gap-1"
            >
              <img src="/python-logo.png" alt="Python" className="w-4 h-4" />
              Python
            </Button>
            <Button
              size="sm"
              variant={selectedLanguage === "javascript" ? "default" : "outline"}
              onClick={() => setSelectedLanguage("javascript")}
              className="flex items-center gap-1"
            >
              <img src="/js-logo.png" alt="JavaScript" className="w-4 h-4" />
              Javascript
            </Button>
            <Button
              size="sm"
              variant={selectedLanguage === "bash" ? "default" : "outline"}
              onClick={() => setSelectedLanguage("bash")}
              className="flex items-center gap-1"
            >
              <img src="/bash-logo.png" alt="Bash" className="w-4 h-4" />
              Bash
            </Button>
          </div>

          {/* Installation */}
          <div className="space-y-2">
            <p className="text-sm">
              <span className="font-medium">
                1. {selectedLanguage === "python" && "Install the Python client"}
                {selectedLanguage === "javascript" && "Install the Javascript client"}
                {selectedLanguage === "bash" && "Confirm that you have cURL installed on your system."}
              </span>{" "}
              {selectedLanguage !== "bash" && (
                <>
                  (<a href="#" className="text-primary underline">docs</a>)
                  {selectedLanguage === "python" ? " if you don't already have it installed." : " if you don't already have it installed."}
                </>
              )}
            </p>
            <div className="relative">
              <pre className="bg-muted p-3 rounded text-sm overflow-x-auto">
                <code>
                  {selectedLanguage === "python" && "$ pip install gradio_client"}
                {selectedLanguage === "javascript" && "$ npm i -D @gradio/client"}
                  {selectedLanguage === "bash" && "$ curl --version"}
                </code>
              </pre>
              <Button
                size="sm"
                variant="ghost"
                className="absolute top-2 right-2"
                onClick={() => {
                  const installCmd = selectedLanguage === "python" ? "pip install gradio_client" :
                                 selectedLanguage === "javascript" ? "npm i -D @gradio/client" :
                                   "curl --version";
                  copyToClipboard(installCmd);
                }}
              >
                <Copy className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* API Usage */}
          <div className="space-y-2">
            <p className="text-sm">
              <span className="font-medium">2. Find the API endpoint below</span> corresponding to your desired function in the app. Copy the code snippet, replacing the placeholder values with your own input data. Or use the{" "}
            <Badge variant="outline" className="inline-flex items-center gap-1">
              <div className="w-2 h-2 bg-red-500 rounded-full"></div>
              API Recorder
            </Badge> to automatically generate your API requests.
          </p>
          {selectedLanguage === "bash" && (
            <p className="text-sm text-muted-foreground">
              Making a prediction and getting a result requires 2 requests: a POST and a GET request. The POST request returns an EVENT_ID, which is used in the second GET request to fetch the results. In these snippets, we've used awk and read to parse the results, combining these two requests into one command for ease of use. See curl docs.
            </p>
          )}
          </div>

          {/* API Endpoints */}
          <div className="space-y-6">
            {apiEndpoints.map((endpoint, index) => (
              <div key={index} className="border rounded p-4 space-y-4">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm">api_name:</span>
                <Badge variant="secondary" className="text-[#10B981] bg-[#10B981]/10 border-[#10B981]/20">{endpoint.name}</Badge>
                </div>

                <p className="text-sm text-muted-foreground">{endpoint.description}</p>

                <div className="relative">
                  <pre className="bg-muted p-3 rounded text-sm overflow-x-auto">
                    <code>
                      {selectedLanguage === "python" && endpoint.python}
                      {selectedLanguage === "javascript" && endpoint.javascript}
                      {selectedLanguage === "bash" && endpoint.bash}
                    </code>
                  </pre>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="absolute top-2 right-2"
                    onClick={() => {
                      const currentCode = selectedLanguage === "python" ? endpoint.python :
                                        selectedLanguage === "javascript" ? endpoint.javascript :
                                        endpoint.bash;
                      copyToClipboard(currentCode);
                    }}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>

                <div className="space-y-2">
                  <div className="text-sm">
                  <span className="font-medium">
                    → Accepts {endpoint.parameter.name === "none" ? "0" : endpoint.parameter.name === "25 parameters" ? "25" : "1"} parameter{endpoint.parameter.name === "none" || endpoint.parameter.name === "25 parameters" ? "s" : ""}:
                  </span>
                  </div>
                {endpoint.parameter.name !== "none" && endpoint.parameter.name !== "25 parameters" && (
                  <div className="pl-4 space-y-1 text-sm">
                    <div>
                      <Badge variant="outline" className="mr-2">{endpoint.parameter.name}</Badge>
                      <code className="text-xs bg-muted px-1 rounded text-[#10B981]">
                        {endpoint.parameter.type}
                      </code>
                      <span className="text-muted-foreground ml-2">Default: *{endpoint.parameter.default}*</span>
                    </div>
                    <p className="text-muted-foreground text-xs">
                      {endpoint.parameter.description}
                    </p>
                  </div>
                )}
                {endpoint.parameter.name === "25 parameters" && detailedParameters[endpoint.name] && (
                  <div className="pl-4 space-y-1 text-sm">
                    {detailedParameters[endpoint.name].map((param, idx) => (
                      <div key={idx} className="border-b border-border pb-2">
                        <div>
                          <Badge variant="outline" className="mr-2">{param.name}</Badge>
                          <code className="text-xs bg-muted px-1 rounded text-[#10B981]">
                            {param.type}
                          </code>
                          <span className="text-muted-foreground ml-2">Default: *{param.default}*</span>
                        </div>
                        <p className="text-muted-foreground text-xs mt-1">
                          {param.description}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
                </div>

                <div className="space-y-2">
                  <div className="text-sm">
                  <span className="font-medium">
                    → Returns {endpoint.returns.type.includes("tuple") ? "tuple of 13 elements" : endpoint.returns.type.includes("list") ? "list of 13 elements" : "1 element"}
                  </span>
                  </div>
                  <div className="pl-4 space-y-1 text-sm">
                    <div>
                    <Badge variant="outline" className="text-[#10B981] bg-[#10B981]/10 border-[#10B981]/20">{endpoint.returns.type}</Badge>
                    </div>
                    <p className="text-muted-foreground text-xs">
                      {endpoint.returns.description}
                    </p>
                  {returnValues[endpoint.name] && (
                    <div className="mt-2 space-y-1">
                      {returnValues[endpoint.name].map((ret, idx) => (
                        <div key={idx} className="text-xs">
                          <span className="font-mono">{ret.index}</span>{" "}
                          <code className="bg-muted px-1 rounded text-[#10B981]">{ret.type}</code>
                          <p className="text-muted-foreground mt-1">
                            {ret.description}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                  </div>
                </div>
              </div>
            ))}
          </div>
      </div>
    </ScrollArea>
  );
};
