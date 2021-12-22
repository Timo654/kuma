import modules.parsers.oe.kara_reader as kara


def get_vert_pos(note):
    if note == 0:
        return 4
    elif note == 1:
        return 6
    elif note == 2:
        return 2
    elif note == 3:
        return 0

def convert_button(button):
    if button == 0:
       return 1
    elif button == 1:
        return 0
    elif button == 4: # arrows
        return 1
    elif button == 5:
        return 2
    else:
        return button

def convert_to_kbd(data):
    kbd = dict()

    # HEADER
    kbd['Header'] = dict()
    kbd['Header']['Magic'] = "NTBK"
    kbd['Header']['Version'] = 2
    kbd['Header']['Note count'] = 0
    kbd['Header']['Max score'] = 0
    kbd['Header']['Max score pre-cutscene'] = 0

    # get the notes from the lines
    notes = list()
    for i in range(len(data['Lines'])):
        for o in range(len(data['Lines'][i]['Notes'])):
            note = data['Lines'][i]['Notes'][o]

            #If Unknown 15 is 0, Line length has to be divided by 2 to get the max percentage, otherwise it has to be divided by 24.
            if not data['Lines'][i]['Unknown 15']:
                max_percent = data['Lines'][i]['Settings']['Line length'] / 2
            else: 
                max_percent = data['Lines'][i]['Settings']['Line length'] / 24 

            #To get the actual start and end (relative to current line) percentage of a note, divide the "Start Position" by max percentage
            start_pos =  note['Start position'] / max_percent
            end_pos = note['End position'] / max_percent

            #Calculating line length (milliseconds) by subtracting start time from end time
            line_length = data['Lines'][i]['Settings']['Line end time (ms)'] - data['Lines'][i]['Settings']['Line start time (ms)']
            #Calculating the actual start pos of a note by multiplying the line length with the start pos percentage and then adding that to the line start time. (milliseconds)
            actual_s_pos = data['Lines'][i]['Settings']['Line start time (ms)'] + (line_length * start_pos)

            if note['End position'] > 0:  
                actual_e_pos = data['Lines'][i]['Settings']['Line start time (ms)'] + (line_length * end_pos)
            else:
                actual_e_pos = 0 
            note = (int(actual_s_pos * 3), int(actual_e_pos * 3), note['Button type'], note['Note type'])
            notes.append(note)

        notes_list = list()
        # update pointers
        for note in notes:
            newnote = dict()
            newnote['Start position'] = note[0]
            newnote['End position'] = note[1]
            newnote['Button type'] = convert_button(note[2])
            newnote['Vertical position'] = get_vert_pos(newnote['Button type'])
            newnote['Note type'] = note[3]
            newnote['Cue ID'] = 0
            newnote['Cuesheet ID'] = 0
            notes_list.append(newnote)

        kbd['Notes'] = notes_list

    return kbd


def load_kara(file):
    data = kara.read_file(file)
    return convert_to_kbd(data)
