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
        "-i",
        audio_input,
        "-filter_complex",
        #f"loudnorm=measured_I={loudness_values['input_i']}:measured_TP={loudness_values['input_tp']}:measured_LRA={loudness_values['input_lra']}:measured_thresh={loudness_values['input_thresh']}:I=-12.0:LRA=3.0:TP=-1.0,,highpass=f=70,lowpass=f=10000,arnndn=m=rnnoise-models-master/conjoined-burgers-2018-08-28/cb.rnnn",
        f"highpass=f=80,lowpass=f=6000,equalizer=f=1000:t=q:w=1.5:g=6,equalizer=f=3000:t=q:w=2:g=4,loudnorm=measured_I={loudness_values['input_i']}:measured_TP={loudness_values['input_tp']}:measured_LRA={loudness_values['input_lra']}:measured_thresh={loudness_values['input_thresh']}:I=-12.0:LRA=6.0:TP=-2.0",
        "-c:a", 
        "pcm_s24le", # PCM little-endian 24 bit 
        "-ar", 
        "48000", # 48 kHz sample rate
        "-ac",
        "2", # Mono or stereo output
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
