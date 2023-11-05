import os
import json
import pandas as pd
import openai
import panel as pn  # GUI
from dotenv import load_dotenv, find_dotenv
import speech_recognition as sr
from gtts import gTTS
from pygame import mixer
import tempfile
import time
openai.api_key  = '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'

def Check(info):
    if info["name"] == "XXX":
        return "What is your name?"
    elif info["location"] == "XXX":
        return "Where are you?"
    elif info["type"] == "XXX":
        return "What is the emergency?"
    elif info["symptoms"] == "XXX":
        return "What are the symptoms?"
    else:
        return None

def AtoT():
    # Initialize recognizer class (for recognizing the speech)
    r = sr.Recognizer()

    # use the microphone as source for input. Here, we also specify
    # which device ID to specifically look for incase the microphone
    # is not working, an error will pop up saying "device_id undefined"
    with sr.Microphone() as source:
        print("Talk")
        audio_text = r.listen(source, timeout=5, phrase_time_limit=10)
        print("Time over, thanks")
    # recoginize_() method will throw a request error if the API is unreachable, hence using exception handling

        try:
            # using google speech recognition
            print("Text: "+r.recognize_google(audio_text))
            return r.recognize_google(audio_text)
        except:
            print("Sorry, I did not get that")

def text_to_speech(text):
    # Convert text to speech
    tts = gTTS(text=text, lang='en')

    # Save the audio file
    with tempfile.NamedTemporaryFile(delete=True) as fp:
        tts.save("{}.mp3".format(fp.name))
        return fp.name

def play_audio(file):
    # Initialize the mixer
    mixer.init()

    # Load the audio file
    mixer.music.load(file + ".mp3")

    # Play the audio file
    mixer.music.play()
    while mixer.music.get_busy():  # wait for the audio to finish
        time.sleep(0.1)

def translate(text):
    # text = "9 1 1, what's your emergency?"
    audio_file = text_to_speech(text)
    play_audio(audio_file)

def get_emergency_info(call, name_list,  cur_info, model="gpt-3.5-turbo"): 
    prompt = f"""role':'system', 'content':
            Get information from the following text ```{call}``` and ```{cur_info}`` in an emergency caller\
            1. name of the caller: use the list in```{name_list}``` and get the name
               if the actual name getting from the text does not match, then choose the most similar one of the first name
            2. emergency types: FIRE CALLS, POLICE CALLS, EMS CALLS\
            3. the incident location (as short as possible)\
            4. the symptoms (as short as possible)\

            Note:
            if any of the information is not available, put XXX as the value.\
            if all the information has a value
            
            Output:
            save all the information in JSON format, with the key: name, type, location, symptoms\
            """
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0,
    )
    return response.choices[0].message["content"]

def get_sug(prompt, model="gpt-3.5-turbo"):
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0,
    )
    return response.choices[0].message["content"]

################################################################################################################

filename = 'new_hacks_2023.json'
keep_talking = 1
say = "9 1 1, what's your emergency?"
df = pd.read_json(filename)
name_list = df['first_name']
cur_info = ''

while keep_talking == 1:
    translate(say)

    # receive audio input
    #input = AtoT()
    #print(input)

    input = """
        My name is Amy. My friend fell down the stairs. Her ankle is swollen and 
        her nose is bleeding. We are in 100 College St.\
    """

    # send to AI Text Processing 
    response = get_emergency_info(input, cur_info, name_list)
    cur_info = response
    response_js = json.loads(response)
    print(response_js)
    print(type(response_js))

    say = Check(response_js)
    if say == None:
        keep_talking = 0

index = (list(name_list)).index(response_js.get('name'))
df_information = df.iloc[index]
print(df_information)

# hospital information
prompt_hos = f"""role':'system', 'content':
            Get information from the following dataframe ```{df_information}``` and ```{response_js}``` base on an emergency caller\
            provide two specific suggestions each less than 20 words for the hospital to prepare\
            
            Output:
            in JSON style\
            """
hos_sug = get_sug(prompt_hos)
print(hos_sug)

#ambulence information
prompt_amb = f"""role':'system', 'content':
            Get information from the following dataframe ```{df_information}``` and ```{response_js}``` base on an emergency caller\
            provide two specific suggestions each less than 20 words for the coming ambulence to prepare\
            template of specific suggestions could be certain equipment and action\
            
            Output:
            in JSON style\
            """
amb_sug = get_sug(prompt_amb)
print(amb_sug)

#for family
prompt_fam = f"""role':'system', 'content':
            Get information from the following dataframe ```{df_information}```, ```{df}``` and base on an emergency caller\
            and write a message to the family group with the same family_id\
            briefly explain the current situation based on ```{response_js}``` in kind and concise language\
            and inform them to come to hospital\
            
            Output:
            in JSON style\
            """
fam_sug = get_sug(prompt_fam)
print(fam_sug)

    