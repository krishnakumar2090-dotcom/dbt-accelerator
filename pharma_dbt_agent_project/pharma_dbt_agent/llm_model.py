from langchain_openai import AzureChatOpenAI

def init_llm(incubator_key, endpoint, api_version):
    """
    Initialize AzureChatOpenAI LLM
    """
    llm = AzureChatOpenAI(
        azure_endpoint=endpoint,
        api_key=incubator_key,
        api_version=api_version,
        model="gpt-4o",
        temperature=0
    )
    return llm
