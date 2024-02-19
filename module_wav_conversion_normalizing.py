# Module functions for (1) normalizing, (2) filtering, (3) denoising and (4) converting to WAV

import subprocess
from subprocess import check_output, CalledProcessError, STDOUT
import json

# This function uses the FFmpeg filter "loudnorm" to measure the loudness of an input file, to normalize it and then to convert it to WAV:
def normalize_extract_audio(audio_input, audio_output):
    # Step 1: Extracting the measured values from the first run:
    measure_cmds = [
        "ffmpeg",
        "-i",
        audio_input,
        "-filter_complex",
        "loudnorm=print_format=json",
        "-f",
        "null",
        "-"]
    try:
        output = check_output(measure_cmds, stderr=STDOUT).decode('utf8', 'ignore')
        # Searching for the start and end of the JSON part of the output:
        json_str_start = output.find('{')
        json_str_end = output.rfind('}')
        if json_str_start == -1 or json_str_end == -1:
            print("No JSON output in FFmpeg response.")
            return
    
        # Extracting the JSON string: 
        json_str = output[json_str_start:json_str_end+1]
        loudness_values = json.loads(json_str)
        print(loudness_values)
    except CalledProcessError as e:
        print("Error during loudness measurement.")
        print(e.output.decode(encoding="utf-8").strip())
        return
    except json.JSONDecodeError as e:
        print("Failed to parse JSON output from loudness measurement.")
        print("JSON Decode Error:", e)
        return

    # Step 2: Using the values in a second run with linear normalization enabled; also using filtering and denoising for audio optimizing:
    extract_cmds = [
        "ffmpeg",
        "-nostdin", # Suppresses interactive inputs to prevent pauses in automated or scripted environments
        "-threads", # Utilizes all available CPU cores for increased processing efficiency
        "0",
        "-i",
        audio_input,
        "-filter_complex",
        #f"loudnorm=measured_I={loudness_values['input_i']}:measured_TP={loudness_values['input_tp']}:measured_LRA={loudness_values['input_lra']}:measured_thresh={loudness_values['input_thresh']}:I=-12.0:LRA=3.0:TP=-1.0,highpass=f=70,lowpass=f=10000,arnndn=m=rnnoise-models-master/conjoined-burgers-2018-08-28/cb.rnnn",
        f"loudnorm=measured_I={loudness_values['input_i']}:measured_TP={loudness_values['input_tp']}:measured_LRA={loudness_values['input_lra']}:measured_thresh={loudness_values['input_thresh']}:I=-12.0:LRA=3.0:TP=-1.0,highpass=f=80,lowpass=f=6000,equalizer=f=1000:t=q:w=1.5:g=6,equalizer=f=3000:t=q:w=2:g=4", # I default value is -24.0, LRA default value is 7.0, TP default value is -2.0. 
        "-c:a", 
        "pcm_s16le", # Pulse-Code Modulation bit rate little-endian -> Per default, Whisper uses pcm_s16le. 
        "-ar", 
        "16000", # Sample rate -> Per default, Whisper resamples the input audio to 16kHz.
        "-ac",
        "1", # Mono or stereo output -> Per default, Whisper uses mono. 
        "-y",
        audio_output
    ]

    try:
        # Start the process with subprocess.Popen and wait until it is finished: 
        subprocess.run(extract_cmds, check=True, stderr=subprocess.PIPE)
        # After successfull normalization we do not need the normal output. 
        final_output = "Loudness normalization and conversion to WAV completed."
    except CalledProcessError as e:
        error_message = e.stderr.decode(encoding="utf-8").strip() if e.stderr else "Unknown error"
        print("Error during loudness normalization:", error_message)
        return None, None

    return final_output, loudness_values



def simple_normalize_audio(input_audio, output_audio):
    try:
        # Define the filter chain for loudness normalization
        filter_chain = 'loudnorm=I=-12.0:LRA=3.0:TP=-1.0'
        #filter_chain += ',equalizer=f=1000:t=q:w=1.5:g=6'
        #filter_chain += ',equalizer=f=3000:t=q:w=2:g=4'

        cmd = [
            'ffmpeg',
            '-y',  # This tells FFmpeg to overwrite the output file without asking
            '-i', 
            input_audio,  # Specify the input audio file
            '-filter:a', 
            filter_chain,  # Apply the filter chain
            "-c:a", 
            "pcm_s16le", # Pulse-Code Modulation bit rate little-endian -> Per default, Whisper uses pcm_s16le. 
            "-ar", 
            "16000", # Sample rate -> Per default, Whisper resamples the input audio to 16kHz.
            "-ac",
            "1", # Mono or stereo output -> Per default, Whisper uses mono. 
            output_audio  # Specify the output audio file
        ]

        subprocess.run(cmd, check=True)
        print(f"Audio processed with loudness normalization. Output saved to: {output_audio}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred during audio processing: {e}")
