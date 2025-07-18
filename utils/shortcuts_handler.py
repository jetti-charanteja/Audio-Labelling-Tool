# shortcuts_handler.py

def bind_shortcuts(root, app):
    root.bind('<space>', lambda event: app.play_audio())
    root.bind('<Return>', lambda event: app.save_label())
    root.bind('<Control-Right>', lambda event: app.next_audio())
    root.bind('<Control-Left>', lambda event: app.previous_audio())

    # Optional: quick label application (1-9 keys map to labels)
    label_keys = {
        '1': "Speech",
        '2': "Noise",
        '3': "Music",
        '4': "Happy",
        '5': "Sad",
        '6': "Angry",
        '7': "English",
        '8': "Telugu"
    }

    for key, label in label_keys.items():
        root.bind(key, lambda e, lbl=label: toggle_label(app, lbl))

def toggle_label(app, label):
    var = app.label_vars.get(label)
    if var is not None:
        var.set(0 if var.get() == 1 else 1)

def add_navigation_methods_to(app):
    def next_audio():
        app.current_index += 1
        if app.current_index >= len(app.audio_files):
            app.current_index = len(app.audio_files) - 1

    def previous_audio():
        app.current_index -= 1
        if app.current_index < 0:
            app.current_index = 0

    app.next_audio = next_audio
    app.previous_audio = previous_audio
