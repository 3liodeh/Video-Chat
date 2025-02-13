import os
import glob
import ast
from transcription import (
    download_audio,
    transcribe_audio,
    split_transcription_into_chunks,
    sanitize_filename
)
from LLM import initialize_llm, process_query, llama_generate_response


def Llama(Human, AI):
    try:
        model_Llama_respose = llama_generate_response(Human, AI)
    except Exception as e:
        return f"Error in Llama: {e}"
    return model_Llama_respose
    

def return_verification(UserQuery,VideoName):
    relative_check = """You are an advanced artificial intelligence, and your task is to analyze the relationship between the video title provided to you and the user request. If you find any connection between them, whether direct or indirect, respond clearly with "Yes" If there is no relationship at all, your response should be "No" You must not respond with anything other than "Yes" or "No" definitively, and without any additional comments."""
    Query = f"video name:{VideoName}. user request:{UserQuery}."
    relative_reslut = Llama(Query, relative_check)
    
    if relative_reslut.lower() == "yes":
        return True
    elif relative_reslut.lower() == "no":
        return False
    else:
        return f"smothing error in return verification: {relative_reslut}"
        


def Request_verification(UserQuery):
    Request_check = """You are a linguistic AI specialized in deep understanding of speech. Your task is to evaluate the incoming request to determine whether the user is asking for the full text to be returned or not. Regardless of the language the user uses, you should always respond in English. Your response must be strict and precise, limited to either 'Yes' or 'No' with no additions or modifications."""
    Request_reslut = Llama(UserQuery, Request_check)
    
    if Request_reslut.lower() == "yes":
        return True
    elif Request_reslut.lower() == "no":
        return False
    else:
        return f"smothing error in return Request check: {Request_reslut}"
    
    

def Chat(YoutubeVedioUrl, Query, Model, Memory):
    
    #------------extract audio---------------
    audio_files = glob.glob("*.mp3")
    YoutubeVedioUrl_name = sanitize_filename(YoutubeVedioUrl)
    for audio in audio_files:
        url_name = audio.split("#&$$&#")[0]
        if url_name == YoutubeVedioUrl_name:
            audio_name = audio
            break
    else:
        audio_name = download_audio(YoutubeVedioUrl)
          
        if  audio_name.split(" ")[0] == "Invalid URL":
            return audio_name
    
    #------------transcribe audio---------------
    if not os.path.exists(f"{audio_name}.txt"):
        transcribed = transcribe_audio(audio_name)
        
        if isinstance(transcribed,str):
            return transcribed
        
        chunksed_text = split_transcription_into_chunks(transcribed)
        with open(f"{audio_name}.txt","w",encoding ="utf-8") as file:
            file.write(str(chunksed_text))
            file.flush()


    #------------load chunks---------------
    with open(f"{audio_name}.txt","r") as file:
        transcribed_text_from_txt = ast.literal_eval(file.read())
            

    
    #---------Verifying if the user requests a specific text return----------
    vedio_name = audio_name.split("#&$$&#")[1]
    relative_verification = return_verification(Query,vedio_name)
    


    if relative_verification not in [True, False]:
        return relative_verification
    
    #------------chat processing---------------
    if relative_verification == True:


        
        #----------Verifying if the user requests a All text return------------
        return_request = Request_verification(Query)
        if return_request not in [True, False]:
            return relative_verification
        
        if return_request == True:
            return transcribed_text_from_txt
        else:

            #------------return the closest texts---------------
            Demand_output = process_query(transcribed_text_from_txt, Query)
            
            memory_variables = Memory.load_memory_variables({})
            
            Model_Response = Model.invoke({"history": memory_variables.get("history", ""), "question": f"The text closest to the question: {Demand_output}\nQuestion: {Query}"})
            
            Memory.save_context({"question": f"The text closest to the question: {Demand_output}\nQuestion: {Query}"}, {"response": Model_Response})
            
            
            return Model_Response
            
            
    else:
        return "Your question is not related to the video content."
            

        