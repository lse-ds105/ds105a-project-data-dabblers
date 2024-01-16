import webbrowser
import os

# After saving the file with save(p)
filename = 'interactive_plot.html'
file_path = os.path.abspath(filename)

# Open a browser window with the plot
webbrowser.open('file://' + file_path)
