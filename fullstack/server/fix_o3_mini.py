import browser_use.agent.service

original_set_tool_calling_method = browser_use.agent.service.Agent._set_tool_calling_method

def patched_set_tool_calling_method(self):
    tool_calling_method = self.settings.tool_calling_method
    if tool_calling_method == 'auto':
        if 'deepseek-reasoner' in self.model_name or 'deepseek-r1' in self.model_name:
            return 'raw'
        elif 'o3-mini' in self.model_name or 'o3' in self.model_name:
            return 'raw'
        elif self.chat_model_library == 'ChatGoogleGenerativeAI':
            return None
        elif self.chat_model_library == 'ChatOpenAI':
            return 'function_calling'
        elif self.chat_model_library == 'AzureChatOpenAI':
            return 'function_calling'
        else:
            return None
    else:
        return tool_calling_method

browser_use.agent.service.Agent._set_tool_calling_method = patched_set_tool_calling_method