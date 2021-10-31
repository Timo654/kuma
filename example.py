import kbd_reader as kbd
import kpm_reader as kpm

test_kbd = ".//test_files//tonight_normal_btn.kbd"
test_kpm = ".//test_files//tonight_param.kpm"
andmed_kbd = kbd.read_file(test_kbd)
for note in andmed_kbd['Notes']:
    print((note['Start position'] / 3) / 1000)

andmed_kpm = kpm.read_file(test_kpm)
for param in andmed_kpm['Parameters']:
    print('Cutscene start time:', param['Cutscene start time'])