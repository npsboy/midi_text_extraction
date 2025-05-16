import mido
import json
import sys
import time


song_file = r"In the Hall of the Mountain King.mid" # path to the midi file
midi = mido.MidiFile(song_file)
print("MIDI file loaded successfully.")
main_track = midi.tracks[0]

important_events = [] # list of all note on and off events
notes_list = [] # list with start and end times of notes, overlapping notes are removed later
buzzer_list = [] #final list for the buzzer. format: [frequency, duration in seconds]


# gets the main note on and off events and timestamps them
def extract_and_timestamp_events ():
    time = 0
    for event in main_track:

        time = time + event.time

        if event.type == 'note_on' or event.type == 'note_off':
            event_details = {"type": event.type, "note": event.note, "velocity": event.velocity, "time": time}
            important_events.append(event_details)

        #if len(important_events) > 10:
        #    break
    


def group_note_on_off ():
    for event in important_events:
        if event["type"] == "note_on":
            #sets note info based on 'note_on' event
            note_info = {"note": event["note"], "velocity":event["velocity"], "start_time": event["time"]}

            #cycles through the other notes to find the corresponding 'note_off' event
            for potential_match in important_events:

                if potential_match["type"] == "note_off" and potential_match["note"] == event["note"]:
                    note_info["end_time"] = potential_match["time"]

                    important_events.remove(potential_match)  # Remove the matched note_off event
                    #important_events.remove(event)  # Remove the matched note_on event
                    break
            if "end_time" in note_info:
                notes_list.append(note_info)
    if notes_list == []:
        print("No notes in file / note_off not found")
        sys.exit()

def remove_overlapping_notes ():
    i = 1
    while i < len(notes_list):
        if notes_list[i]["start_time"] < notes_list[i-1]["end_time"]:
            notes_list[i-1]["end_time"] = notes_list[i]["end_time"]
            #if notes_list[i]["velocity"] > notes_list[i-1]["velocity"]:
            #    notes_list.remove(notes_list[i-1])
            #elif notes_list[i]["velocity"] < notes_list[i-1]["velocity"]:
            #    notes_list.remove(notes_list[i])
            #else:
            #    notes_list.remove(notes_list[i-1])
            #i = i - 1

        i = i + 1

def get_frequency (note):
    midi_number = note["note"]
    frequency = 440 * 2 ** ((midi_number - 69) / 12)
    return frequency

def find_second_per_tick ():
    tempo = 0 # microseconds per quater note
    for event in main_track:
        if event.type == "set_tempo":
            tempo = event.tempo

    ppq = midi.ticks_per_beat # ticks per quarter note

    seconds_per_tick = (tempo / 1000000 ) / ppq
    return seconds_per_tick

def convert_to_freq_and_time ():
    ms_per_tick = find_second_per_tick()
    i = 0
    while i < len(notes_list):
        note = notes_list[i]
        
        buzzer_note = {}

        if  i > 0 and notes_list[i-1]["end_time"] < note["start_time"]:
            time.sleep(0)
            empty_space = note["start_time"] - notes_list[i-1]["end_time"]
            buzzer_note["frequency"] = 0
            buzzer_note["duration"] = empty_space * ms_per_tick
            buzzer_list.append(buzzer_note.copy())

        buzzer_note["frequency"] = get_frequency(note)

        duration = (note["end_time"] - note["start_time"])
        buzzer_note["duration"] = duration * ms_per_tick

        buzzer_list.append(buzzer_note.copy())

        i = i + 1
    

def main ():
    extract_and_timestamp_events()
    group_note_on_off()
    remove_overlapping_notes()
    convert_to_freq_and_time()
    print("Notes List:")
    for note in buzzer_list:
        print(note)
    
    with open("buzzer_notes.json", "w") as file:
        json.dump(buzzer_list, file)

main()  