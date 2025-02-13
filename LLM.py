from langchain_huggingface import HuggingFaceEndpoint
from langchain.memory import ConversationSummaryBufferMemory
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import os

load_dotenv()


token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
inference_client = InferenceClient(api_key=token)


def llama_generate_response(user_input, system_prompt, 
                            model="meta-llama/Llama-3.2-3B-Instruct", 
                            temperature=0.8, max_tokens=2048, top_p=0.3):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"text: {user_input}"}
    ]
    try:
        stream = inference_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=True
        )
        return "".join([chunk.choices[0].delta.content for chunk in stream])
    except Exception as error:
        return f"An error occurred: {error}"
    
def evaluate_similarity(transcription_chunks, user_query):
    similarity_scores = []
    for timestamp, text in transcription_chunks.items():
        prompt = f"""Text: [The sentence was said in {timestamp} seconds: {text}].\nQuery: {user_query}"""
        ai_prompt = """You are an advanced artificial intelligence model designed to evaluate the relevance of a given question to a specific text. Based on two inputs—a question and a text—you analyze and compare them to produce a single output: a score between 0 and 100. The output must be strictly a number within this range, with no additional text or explanations. If the user's query involves retrieving text based on a specific time, and the evaluated sentence aligns with this request, you should increase its relevance score accordingly."""
        response = llama_generate_response(prompt, ai_prompt)
        similarity_scores.append((response, text))
    return similarity_scores
    

def initialize_llm(repo_id="mistralai/Mistral-Nemo-Instruct-2407", temperature=0.8, max_length=4096, max_token_limit=4096):
    """Initialize the LLM model and conversation memory."""
    
    llm = HuggingFaceEndpoint(
        repo_id=repo_id,
        temperature=temperature,
        model_kwargs={"max_length": max_length}
    )
    
    memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=max_token_limit)


    prompt = PromptTemplate(
        input_variables=["question"],
        template="""You are an AI assistant called ChatWithVideo. The user will provide a request, and based on it,\n you will receive text corresponding to the content of a video. Your task is to respond appropriately using both\n the provided text and your own knowledge.\nCurrent conversation:\nHuman: {question}\n AI"""
    )

    chain = prompt | llm | StrOutputParser()

    return chain, memory

def process_query(texts, query):
    """Process the query and return the most relevant content."""

    rating = evaluate_similarity(texts, query)
    sorted_rates = sorted(rating, reverse=True, key=lambda x: int(x[0]))

    content = [rate[1] for rate in sorted_rates if int(rate[0]) >= 80]
    return " ".join(content) if content else sorted_rates[0][1]
